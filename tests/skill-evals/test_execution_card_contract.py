"""Deterministic composer and validator for complete scene execution cards."""

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path


CJK_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF]")
SCENE_HEADER_RE = re.compile(r"^## 场景([1-4])｜篇幅权重：(短|中|长)$")
FIELD_LINE_RE = re.compile(r"^\s*-\s*([^：:\r\n]+)[：:](.*)$")
NUMBERED_RE = re.compile(r"^\s*([1-9]\d*)\.\s+(.+?)\s*$")
ATX_RE = re.compile(r"(?m)^[ ]{0,3}(#{1,6})[ \t]+(.+?)[ \t]*$")
TASK_BLOCK_RE = re.compile(
    r"(?i)^(?:"
    r"#{1,6}|"
    r">|"
    r"[-+*]\s+|"
    r"\d+[.)]\s+|"
    r"`{3,}|~{3,}|"
    r"<h[1-6](?:\s|>)|"
    r"(?:-{3,}|\*{3,}|_{3,})\s*$"
    r")"
)
SCENE_FIELDS = (
    "起始刺激",
    "眼前动作",
    "推进节点",
    "视角偏压",
    "场景结果",
    "衔接方式",
)
SCENE_WEIGHTS = {"短", "中", "长"}
ENDING_HEADING = "结尾落点"
FORBIDDEN_RAW_LABELS = ("连续性锁定", "禁止扩写", ENDING_HEADING, "放行结论")
FIXTURE_KEYS = {"case_id", "title", "expected_scenes", ENDING_HEADING}
CONCLUSION_VALUES = {
    "新增重要事件": "否",
    "改变细纲结果": "否",
    "提前揭示后续": "否",
    "结尾落点一致": "是",
}
RELEASE_KEYS = {"raw_sha256", *CONCLUSION_VALUES}
RELEASE_CHECK_KEYS = {
    f"{case_id}/run-{run}.txt"
    for case_id in ("01", "04", "06")
    for run in range(1, 6)
}
PLACEHOLDER_RE = re.compile(
    r"(?i)(?:"
    r"(?<![A-Za-z])(?:TODO|TBD|PLACEHOLDER)(?![A-Za-z])|"
    r"(?m:^[ \t]*(?:待填写|待补充|此处填写|占位符|模板说明|模板占位))|"
    r"(?m:^\s*请(?:在这里|在此处|于此处)?(?:填写|补充))|"
    r"[【\[]\s*(?:待填写|待补充|TODO|TBD|PLACEHOLDER|占位符)\s*[】\]]|"
    r"<\s*(?:待填写|待补充|TODO|TBD|PLACEHOLDER|占位符|本章任务|起始刺激|眼前动作|推进节点|视角偏压|场景结果|衔接方式|结尾落点)(?:[：:][^>]*)?\s*>|"
    r"用一句话说明本章必须完成什么|"
    r"用一句话写明要处理的眼前问题和必须出现的可见结果|"
    r"如果本章只需要两个场景，可以省略本节|"
    r"正在发生的动作、声音、物件或可见阻力，不写抽象局势|"
    r"视角人物本场立即要做成的具体动作|"
    r"动作或外部反馈|"
    r"人物被迫选择或调整|"
    r"动作造成的可见后果；同义说明不得拆成多个节点|"
    r"写既有偏压如何在本场改变注意、判断或动作；无则写“无”|"
    r"先写镜头可见的变化，不写方法总结|"
    r"用未完成动作、新压力、消息或决定撞入下一场|"
    r"具体到最后的画面、动作、信息或情绪"
    r")"
)
EMBEDDED_AUDIT_LABEL_RE = re.compile(r"(?:连续性锁定|禁止扩写|放行结论)\s*[：:]")


class CardContractError(ValueError):
    """Raised when a card does not satisfy the frozen mechanical contract."""


def _strict_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CardContractError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _load_strict_json(path, invalid_message):
    try:
        return json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_strict_json_object,
        )
    except CardContractError:
        raise
    except (json.JSONDecodeError, UnicodeError, OSError) as exc:
        raise CardContractError(invalid_message) from exc


def _sections(markdown):
    parts = re.split(r"(?m)^##\s+(.+?)\s*$", markdown)
    if len(parts) == 1:
        return [], markdown
    return list(zip(parts[1::2], parts[2::2])), parts[0]


def _atx_headings(markdown):
    return [(len(match.group(1)), match.group(2).strip()) for match in ATX_RE.finditer(markdown)]


def _single_line(value):
    return type(value) is str and bool(value.strip()) and "\n" not in value and "\r" not in value


def _validate_fixture(fixture, expected_case_id=None):
    if type(fixture) is not dict or set(fixture) != FIXTURE_KEYS:
        raise CardContractError("fixture top-level keys are not exact")
    if type(fixture["case_id"]) is not str or not re.fullmatch(r"\d{2}", fixture["case_id"]):
        raise CardContractError("fixture case_id must be two digits")
    if expected_case_id is not None:
        normalized_case = str(expected_case_id).zfill(2)
        if fixture["case_id"] != normalized_case:
            raise CardContractError("fixture case_id does not match")
    if not _single_line(fixture["title"]):
        raise CardContractError("fixture title must be a nonempty single line")
    if type(fixture["expected_scenes"]) is not int or fixture["expected_scenes"] not in (2, 3, 4):
        raise CardContractError("fixture expected_scenes must be 2, 3, or 4")
    if not _single_line(fixture[ENDING_HEADING]):
        raise CardContractError("fixture ending must be a nonempty single line")
    for value in fixture.values():
        if type(value) is not str:
            continue
        if PLACEHOLDER_RE.search(value):
            raise CardContractError("fixture string contains a template placeholder")
        if _contains_shell_label(value):
            raise CardContractError("fixture string contains a composer-owned or legacy label")
        if EMBEDDED_AUDIT_LABEL_RE.search(value):
            raise CardContractError("fixture string embeds a composer-owned or legacy label")
    return fixture


def _validate_release_record(release_record, skill_output=None):
    if type(release_record) is not dict or set(release_record) != RELEASE_KEYS:
        raise CardContractError("release record keys are not exact")
    raw_sha256 = release_record["raw_sha256"]
    if type(raw_sha256) is not str or not re.fullmatch(r"[0-9a-f]{64}", raw_sha256):
        raise CardContractError("release record raw_sha256 is invalid")
    conclusions = {key: release_record[key] for key in CONCLUSION_VALUES}
    if conclusions != CONCLUSION_VALUES:
        raise CardContractError("release checks did not all pass")
    if skill_output is not None:
        if type(skill_output) is bytes:
            raw_bytes = skill_output
        elif type(skill_output) is str:
            try:
                raw_bytes = skill_output.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise CardContractError("skill output is not valid UTF-8 text") from exc
        else:
            raise CardContractError("skill output must be bytes or text")
        actual_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        if raw_sha256 != actual_sha256:
            raise CardContractError("release record raw_sha256 does not match skill output")
    return release_record


def _decode_skill_output(skill_output):
    if type(skill_output) is bytes:
        try:
            return skill_output.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CardContractError("skill output bytes are not valid UTF-8") from exc
    if type(skill_output) is str:
        try:
            skill_output.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise CardContractError("skill output is not valid UTF-8 text") from exc
        return skill_output
    raise CardContractError("skill output must be bytes or text")


def _contains_shell_label(markdown):
    for line in markdown.splitlines():
        content = line.strip()
        previous = None
        while content != previous:
            previous = content
            content = re.sub(r"^(?:>\s*)+", "", content)
            content = re.sub(r"^\d+[.)]\s+", "", content)
            content = re.sub(r"^[-+*]\s+", "", content)
            content = re.sub(r"^#{1,6}\s*", "", content)
        for label in FORBIDDEN_RAW_LABELS:
            pattern = r"[*_~`]*" + re.escape(label) + r"[*_~`]*\s*(?:[：:].*)?"
            if re.fullmatch(pattern, content):
                return True
    return False


def _next_nonblank(lines, index):
    while index < len(lines) and not lines[index].strip():
        index += 1
    return index


def _validate_scene(section_heading, body, expected_number):
    match = SCENE_HEADER_RE.fullmatch("## " + section_heading)
    if not match:
        raise CardContractError("invalid scene heading: " + section_heading)
    number, weight = int(match.group(1)), match.group(2)
    if number != expected_number:
        raise CardContractError("scene numbers must be continuous")
    if weight not in SCENE_WEIGHTS:
        raise CardContractError("scene weight must be 短, 中, or 长")

    lines = body.splitlines()
    index = 0
    for expected_field in SCENE_FIELDS:
        index = _next_nonblank(lines, index)
        if index >= len(lines):
            raise CardContractError("scene must contain exactly six allowed fields")
        field = FIELD_LINE_RE.fullmatch(lines[index])
        if not field:
            raise CardContractError("scene contains content outside the allowed field blocks")
        label, inline_value = field.groups()
        label = label.strip()
        if label != expected_field:
            raise CardContractError("scene fields must appear once in the allowed order")
        index += 1
        if label == "推进节点":
            if inline_value.strip():
                raise CardContractError("推进节点 must use 3-5 numbered items")
            node_count = 0
            while True:
                candidate = _next_nonblank(lines, index)
                if candidate >= len(lines):
                    index = candidate
                    break
                numbered = NUMBERED_RE.fullmatch(lines[candidate])
                if not numbered:
                    index = candidate
                    break
                node_count += 1
                node_text = numbered.group(2).strip()
                if int(numbered.group(1)) != node_count or not node_text:
                    raise CardContractError("推进节点 must be nonempty and continuously numbered")
                if TASK_BLOCK_RE.match(node_text):
                    raise CardContractError("推进节点 must contain plain content, not a nested block")
                if _contains_shell_label(node_text):
                    raise CardContractError("推进节点 contains a composer-owned or legacy label")
                if PLACEHOLDER_RE.search(node_text):
                    raise CardContractError("推进节点 contains a template placeholder")
                if node_count > 5:
                    raise CardContractError("推进节点 must contain 3-5 numbered items")
                index = candidate + 1
            if node_count < 3:
                raise CardContractError("推进节点 must contain 3-5 numbered items")
        else:
            field_value = inline_value.strip()
            if not field_value:
                raise CardContractError("empty scene field: " + label)
            if _contains_shell_label(field_value):
                raise CardContractError("scene field contains a composer-owned or legacy label")
            if PLACEHOLDER_RE.search(field_value):
                raise CardContractError("scene field contains a template placeholder")

    index = _next_nonblank(lines, index)
    if index != len(lines):
        remaining = lines[index]
        if FIELD_LINE_RE.fullmatch(remaining):
            raise CardContractError("unknown or repeated top-level field")
        raise CardContractError("scene contains content outside the allowed field blocks")
    return weight


def _validate_task_body(body):
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if len(lines) != 1:
        raise CardContractError("chapter task must contain exactly one nonempty line")
    if TASK_BLOCK_RE.match(lines[0]):
        raise CardContractError("chapter task must be one plain content line")


def _validate_raw_skill_output(skill_output, expected_scenes):
    if type(skill_output) is not str:
        raise CardContractError("skill output must be text")
    if _contains_shell_label(skill_output):
        raise CardContractError("skill output fills a shell-owned heading or label")
    headings = _atx_headings(skill_output)
    if len(headings) != expected_scenes + 1 or any(level != 2 for level, _ in headings):
        raise CardContractError("skill output contains an extra or missing ATX heading")
    sections, prefix = _sections(skill_output)
    if prefix.strip():
        raise CardContractError("skill output must not contain an H1 or preamble")
    if len(sections) != expected_scenes + 1:
        raise CardContractError("skill output contains a new or missing H2 field")
    section_headings = [heading.strip() for heading, _ in sections]
    if section_headings[0] != "本章任务":
        raise CardContractError("skill output must start with 本章任务")
    _validate_task_body(sections[0][1])
    for number, (heading, body) in enumerate(sections[1:], 1):
        _validate_scene(heading.strip(), body, number)


def compose_card(skill_output, shell_fixture, release_record):
    """Compose a writer-facing card after the external release gate passes."""
    fixture = _validate_fixture(shell_fixture)
    skill_text = _decode_skill_output(skill_output)
    _validate_raw_skill_output(skill_text, fixture["expected_scenes"])
    _validate_release_record(release_record, skill_output)
    card = "# " + fixture["title"].strip() + "\n\n" + skill_text.strip()
    card += "\n\n## " + ENDING_HEADING + "\n" + fixture[ENDING_HEADING].strip() + "\n"
    return card


def validate_card(card, expected_scenes):
    """Validate a complete card and return its visible CJK character count."""
    if type(expected_scenes) is not int or expected_scenes not in (2, 3, 4):
        raise CardContractError("expected scenes must be 2, 3, or 4")
    if type(card) is not str:
        raise CardContractError("card must be text")
    if PLACEHOLDER_RE.search(card):
        raise CardContractError("template placeholder present")

    headings = _atx_headings(card)
    if len(headings) != expected_scenes + 3:
        raise CardContractError("complete card contains an extra or missing ATX heading")
    if headings[0][0] != 1 or any(level != 2 for level, _ in headings[1:]):
        raise CardContractError("complete card allows one H1 followed only by allowed H2 fields")
    sections, prefix = _sections(card)
    prefix_lines = [line for line in prefix.splitlines() if line.strip()]
    if len(prefix_lines) != 1 or not re.fullmatch(r"#\s+\S.*", prefix_lines[0]):
        raise CardContractError("card must start with exactly one Markdown H1")
    if _contains_shell_label(prefix_lines[0]):
        raise CardContractError("card title contains a composer-owned or legacy label")
    if EMBEDDED_AUDIT_LABEL_RE.search(prefix_lines[0]):
        raise CardContractError("card title embeds a composer-owned or legacy label")
    section_headings = [heading.strip() for heading, _ in sections]
    if len(sections) != expected_scenes + 2:
        raise CardContractError("allowed H2 fields are incomplete or reordered")
    if section_headings[0] != "本章任务" or section_headings[-1] != ENDING_HEADING:
        raise CardContractError("allowed H2 fields are incomplete or reordered")
    scene_headings = section_headings[1:-1]
    if any(not SCENE_HEADER_RE.fullmatch("## " + heading) for heading in scene_headings):
        raise CardContractError("new or invalid H2 field")

    task_body = sections[0][1]
    _validate_task_body(task_body)
    if _contains_shell_label(task_body):
        raise CardContractError("chapter task contains a composer-owned or legacy label")

    for number, (heading, body) in enumerate(sections[1:-1], 1):
        _validate_scene(heading.strip(), body, number)

    ending_lines = [line.strip() for line in sections[-1][1].splitlines() if line.strip()]
    if len(ending_lines) != 1:
        raise CardContractError("ending must be one nonempty line")
    if _contains_shell_label(ending_lines[0]):
        raise CardContractError("ending contains a composer-owned or legacy label")
    if EMBEDDED_AUDIT_LABEL_RE.search(ending_lines[0]):
        raise CardContractError("ending embeds a composer-owned or legacy label")

    cjk_count = len(CJK_RE.findall(card))
    if not 500 <= cjk_count <= 800:
        raise CardContractError("visible CJK count must be 500-800")
    return cjk_count


def _fixture_path(fixtures, case_id):
    normalized_case = str(case_id).zfill(2)
    path = Path(fixtures) / (normalized_case + ".json")
    if not path.is_file():
        raise CardContractError("fixture missing: " + path.name)
    fixture = _load_strict_json(path, "fixture is invalid JSON: " + path.name)
    return _validate_fixture(fixture, normalized_case)


def _release_checks_path(release_json):
    path = Path(release_json)
    if not path.is_file():
        raise CardContractError("release checks file missing")
    release_checks = _load_strict_json(path, "release checks file is invalid JSON")
    if type(release_checks) is not dict or set(release_checks) != RELEASE_CHECK_KEYS:
        raise CardContractError("release checks top-level keys are not exact")
    for sample_key in sorted(RELEASE_CHECK_KEYS):
        try:
            _validate_release_record(release_checks[sample_key])
        except CardContractError as exc:
            raise CardContractError(f"invalid release record for {sample_key}: {exc}") from exc
    return release_checks


def _case_outputs(root, case_id):
    direct = Path(root) / str(case_id).zfill(2)
    if not direct.is_dir():
        return []
    expected = [direct / f"run-{number}.txt" for number in range(1, 6)]
    expected_set = set(expected)
    unexpected = sorted(path for path in direct.rglob("*") if path not in expected_set)
    if unexpected:
        relative = unexpected[0].relative_to(direct).as_posix()
        raise CardContractError("unexpected case entry: " + relative)
    return [path for path in expected if path.is_file()]


def _require_five_case_outputs(root, case_id):
    outputs = _case_outputs(root, case_id)
    expected_names = {f"run-{number}.txt" for number in range(1, 6)}
    if len(outputs) != 5 or {path.name for path in outputs} != expected_names:
        raise CardContractError("expected exactly run-1.txt through run-5.txt")
    return outputs


def _resolve_run(root, case_id, run_id):
    run = str(run_id).removeprefix("run-").removesuffix(".txt")
    if not re.fullmatch(r"[1-5]", run):
        raise CardContractError("run output not found")
    path = Path(root) / str(case_id).zfill(2) / ("run-" + run + ".txt")
    if path.is_file():
        return path
    raise CardContractError("run output not found")


def _validate_root(validate_root, fixtures, release_checks):
    passed = 0
    for case_id in ("01", "04", "06"):
        try:
            fixture = _fixture_path(fixtures, case_id)
        except (CardContractError, OSError) as exc:
            print("FAIL " + case_id + "/fixture: " + str(exc))
            continue
        try:
            outputs = _require_five_case_outputs(validate_root, case_id)
        except (CardContractError, OSError) as exc:
            print("FAIL " + case_id + ": " + str(exc))
            continue
        for output in outputs:
            try:
                raw = output.read_bytes()
                sample_key = case_id + "/" + output.name
                card = compose_card(raw, fixture, release_checks[sample_key])
                validate_card(card, fixture["expected_scenes"])
            except (CardContractError, OSError, UnicodeError) as exc:
                print("FAIL " + case_id + "/" + output.name + ": " + str(exc))
            else:
                passed += 1
                print("PASS " + case_id + "/" + output.name)
    if passed != 15:
        sys.stdout.flush()
        raise CardContractError("CARD_CONTRACT_FAIL " + str(passed) + "/15")
    print("CARD_CONTRACT_OK 15/15")


def _self_fixture():
    return {
        "case_id": "99",
        "title": "第九章 合成标题",
        "expected_scenes": 2,
        "结尾落点": "主角握紧钥匙站在雨中的门前，决定立即进入旧楼。",
    }


def _self_release_record(raw):
    raw_bytes = raw if type(raw) is bytes else raw.encode("utf-8")
    return {
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        **CONCLUSION_VALUES,
    }


def _self_compose(raw, fixture):
    return compose_card(raw, fixture, _self_release_record(raw))


def _self_raw(scene_count):
    weights = ("短", "中", "长", "中")
    task = "人物核对【旧案】与[已核验]记录，在有限时间内确认线索并承担选择后果。"
    lines = ["## 本章任务", task]
    for number in range(1, scene_count + 1):
        lines.extend(
            [
                f"## 场景{number}｜篇幅权重：{weights[number - 1]}",
                "- 起始刺激：人物收到必须立刻处理的新线索。",
                "- 眼前动作：人物进入现场核对关键事实。",
                "- 推进节点：",
                "  1. 人物核对现场痕迹。",
                "  2. 同伴提出有效反证。",
                "  3. 人物据此调整行动。",
                "- 视角偏压：人物更愿相信能够减轻自身责任的解释。",
                "- 场景结果：线索确认，关系改变。",
                "- 衔接方式：转向下一场行动。",
            ]
        )
    raw = "\n".join(lines)
    fixture = _self_fixture()
    fixture["expected_scenes"] = scene_count
    card = _self_compose(raw, fixture)
    deficit = 520 - len(CJK_RE.findall(card))
    if deficit > 0:
        raw = raw.replace(task, task + "叙" * deficit)
    return raw


def _expect_rejected(label, operation):
    try:
        operation()
    except CardContractError:
        return
    raise AssertionError(label + " was accepted")


def _self_test():
    for scenes in (2, 3, 4):
        fixture = _self_fixture()
        fixture["expected_scenes"] = scenes
        card = _self_compose(_self_raw(scenes), fixture)
        validate_card(card, scenes)

    fixture = _self_fixture()
    composed = _self_compose(_self_raw(2), fixture)
    expected_headings = [
        (1, fixture["title"]),
        (2, "本章任务"),
        (2, "场景1｜篇幅权重：短"),
        (2, "场景2｜篇幅权重：中"),
        (2, ENDING_HEADING),
    ]
    if _atx_headings(composed) != expected_headings:
        raise AssertionError("composer emitted headings outside the writer-facing contract")
    for forbidden_heading in ("连续性锁定", "禁止扩写", "放行结论"):
        if forbidden_heading in {heading for _, heading in _atx_headings(composed)}:
            raise AssertionError("composer emitted a planning-only heading")
    if any(key in composed for key in CONCLUSION_VALUES):
        raise AssertionError("composer leaked the external release record into the card")

    crlf_bytes = _self_raw(2).replace("\n", "\r\n").encode("utf-8")
    crlf_card = compose_card(crlf_bytes, fixture, _self_release_record(crlf_bytes))
    validate_card(crlf_card, 2)
    lf_record = _self_release_record(crlf_bytes.replace(b"\r\n", b"\n"))
    _expect_rejected(
        "CRLF bytes with LF hash",
        lambda: compose_card(crlf_bytes, fixture, lf_record),
    )

    extra_field = _self_raw(2).replace(
        "- 场景结果：", "- 新增标签：不应出现。\n- 场景结果：", 1
    )
    _expect_rejected("unknown scene field", lambda: _self_compose(extra_field, fixture))
    duplicate_field = _self_raw(2).replace(
        "- 场景结果：", "- 视角偏压：重复字段。\n- 场景结果：", 1
    )
    _expect_rejected("duplicate scene field", lambda: _self_compose(duplicate_field, fixture))
    four_nodes = _self_raw(2).replace(
        "  3. 人物据此调整行动。",
        "  3. 人物据此调整行动。\n  4. 同伴确认新的路线。",
        1,
    )
    _self_compose(four_nodes, fixture)
    five_nodes = four_nodes.replace(
        "  4. 同伴确认新的路线。",
        "  4. 同伴确认新的路线。\n  5. 人物承担选择代价。",
        1,
    )
    _self_compose(five_nodes, fixture)
    two_nodes = _self_raw(2).replace(
        "  3. 人物据此调整行动。\n",
        "",
        1,
    )
    _expect_rejected("fewer than three nodes", lambda: _self_compose(two_nodes, fixture))
    six_nodes = five_nodes.replace(
        "  5. 人物承担选择代价。",
        "  5. 人物承担选择代价。\n  6. 场景继续出现额外动作。",
        1,
    )
    _expect_rejected("more than five nodes", lambda: _self_compose(six_nodes, fixture))

    forbidden_label = _self_raw(2) + "\n- 连续性锁定：越权填写。"
    _expect_rejected("legacy card label", lambda: _self_compose(forbidden_label, fixture))
    emphasized_forbidden_label = _self_raw(2).replace(
        "[已核验]记录", "[已核验]记录\n**连续性锁定**：越权填写", 1
    )
    _expect_rejected(
        "emphasized legacy card label",
        lambda: _self_compose(emphasized_forbidden_label, fixture),
    )
    injected_ending = _self_raw(2) + "\n## 结尾落点\n越权结尾。"
    _expect_rejected("raw ending injection", lambda: _self_compose(injected_ending, fixture))
    extra_heading = _self_raw(2).replace(
        "- 视角偏压：", "### 额外标题\n- 视角偏压：", 1
    )
    _expect_rejected("extra ATX heading", lambda: _self_compose(extra_heading, fixture))
    indented_h1 = _self_raw(2).replace(
        "\n## 场景1", "\n # 额外总标题\n## 场景1", 1
    )
    _expect_rejected("indented H1", lambda: _self_compose(indented_h1, fixture))
    indented_h3 = _self_raw(2).replace(
        "\n## 场景1", "\n   ### 额外小标题\n## 场景1", 1
    )
    _expect_rejected("indented H3", lambda: _self_compose(indented_h3, fixture))
    setext_task = _self_raw(2).replace(
        "\n## 场景1", "\n---\n## 场景1", 1
    )
    _expect_rejected("setext heading in chapter task", lambda: _self_compose(setext_task, fixture))
    blockquote_heading = _self_raw(2).replace(
        "\n## 场景1", "\n> # 隐藏标题\n## 场景1", 1
    )
    _expect_rejected(
        "blockquote heading in chapter task",
        lambda: _self_compose(blockquote_heading, fixture),
    )
    complete_with_h1 = _self_compose(_self_raw(2), fixture) + "\n# 额外总标题\n"
    _expect_rejected("extra H1", lambda: validate_card(complete_with_h1, 2))

    fixture_with_extra_key = _self_fixture()
    fixture_with_extra_key["extra"] = "not allowed"
    _expect_rejected(
        "extra fixture key",
        lambda: _self_compose(_self_raw(2), fixture_with_extra_key),
    )
    raw = _self_raw(2)
    wrong_hash = _self_release_record(raw)
    wrong_hash["raw_sha256"] = "0" * 64
    _expect_rejected(
        "release record with wrong hash",
        lambda: compose_card(raw, fixture, wrong_hash),
    )
    failed_check = _self_release_record(raw)
    failed_check["新增重要事件"] = "是"
    _expect_rejected(
        "release record with failed check",
        lambda: compose_card(raw, fixture, failed_check),
    )
    missing_release_key = _self_release_record(raw)
    missing_release_key.pop("改变细纲结果")
    _expect_rejected(
        "release record with missing key",
        lambda: compose_card(raw, fixture, missing_release_key),
    )
    extra_release_key = _self_release_record(raw)
    extra_release_key["extra"] = "not allowed"
    _expect_rejected(
        "release record with extra key",
        lambda: compose_card(raw, fixture, extra_release_key),
    )
    placeholder_fixture = _self_fixture()
    placeholder_fixture["结尾落点"] = "<待填写>"
    _expect_rejected(
        "fixture placeholder",
        lambda: compose_card(raw, placeholder_fixture, _self_release_record(raw)),
    )
    explanation_fixture = _self_fixture()
    explanation_fixture["结尾落点"] = "模板说明：在这里补充结尾。"
    _expect_rejected(
        "fixture template instruction",
        lambda: compose_card(raw, explanation_fixture, _self_release_record(raw)),
    )
    todo_fixture = _self_fixture()
    todo_fixture["结尾落点"] = "状态TODO补充"
    _expect_rejected(
        "fixture TODO placeholder",
        lambda: compose_card(raw, todo_fixture, _self_release_record(raw)),
    )
    raw_instruction = _self_raw(2).replace(
        "人物核对【旧案】与[已核验]记录",
        "模板说明：人物核对【旧案】与[已核验]记录",
        1,
    )
    _expect_rejected(
        "raw template instruction",
        lambda: validate_card(_self_compose(raw_instruction, fixture), 2),
    )
    current_task_instruction = _self_raw(2).replace(
        "人物核对【旧案】与[已核验]记录，在有限时间内确认线索并承担选择后果。",
        "用一句话写明要处理的眼前问题和必须出现的可见结果。",
        1,
    )
    _expect_rejected(
        "current task template instruction",
        lambda: validate_card(_self_compose(current_task_instruction, fixture), 2),
    )
    generic_task_instruction = _self_raw(2).replace(
        "人物核对【旧案】与[已核验]记录，在有限时间内确认线索并承担选择后果。",
        "请在这里填写人物想法。",
        1,
    )
    _expect_rejected(
        "generic fill instruction",
        lambda: validate_card(_self_compose(generic_task_instruction, fixture), 2),
    )
    angle_placeholder = _self_raw(2).replace(
        "人物更愿相信能够减轻自身责任的解释。",
        "<视角偏压>",
        1,
    )
    _expect_rejected(
        "semantic angle placeholder",
        lambda: validate_card(_self_compose(angle_placeholder, fixture), 2),
    )
    nested_audit_heading = _self_raw(2).replace(
        "  1. 人物核对现场痕迹。",
        "  1. ### 放行结论：四项检查通过。",
        1,
    )
    _expect_rejected(
        "nested audit heading",
        lambda: validate_card(_self_compose(nested_audit_heading, fixture), 2),
    )
    audit_ending_fixture = _self_fixture()
    audit_ending_fixture["结尾落点"] = "放行结论：四项检查均已完成。"
    _expect_rejected(
        "audit label in fixture ending",
        lambda: _self_compose(_self_raw(2), audit_ending_fixture),
    )
    generic_scene_instruction = _self_raw(2).replace(
        "人物更愿相信能够减轻自身责任的解释。",
        "请补充视角偏压。",
        1,
    )
    _expect_rejected(
        "generic scene fill instruction",
        lambda: validate_card(_self_compose(generic_scene_instruction, fixture), 2),
    )
    nested_plain_heading = _self_raw(2).replace(
        "  1. 人物核对现场痕迹。",
        "  1. # 额外标题",
        1,
    )
    _expect_rejected(
        "nested plain heading",
        lambda: validate_card(_self_compose(nested_plain_heading, fixture), 2),
    )
    manual_audit_ending = _self_compose(_self_raw(2), fixture).replace(
        fixture["结尾落点"],
        "放行结论：四项检查均已完成。",
        1,
    )
    _expect_rejected(
        "audit label in complete-card ending",
        lambda: validate_card(manual_audit_ending, 2),
    )
    quoted_interface_prompt = _self_raw(2).replace(
        "人物收到必须立刻处理的新线索。",
        "屏幕提示“请填写授权码”，人物转身寻找管理员。",
        1,
    )
    validate_card(_self_compose(quoted_interface_prompt, fixture), 2)
    quoted_pending_status = _self_raw(2).replace(
        "人物收到必须立刻处理的新线索。",
        "屏幕上的状态仍是“待填写”，人物转身寻找管理员。",
        1,
    )
    validate_card(_self_compose(quoted_pending_status, fixture), 2)
    literal_placeholder_story = _self_raw(2).replace(
        "人物收到必须立刻处理的新线索。",
        "界面加载失败，只剩一个灰色占位符，人物转身寻找管理员。",
        1,
    )
    validate_card(_self_compose(literal_placeholder_story, fixture), 2)
    markdown_autolink = _self_raw(2).replace(
        "人物收到必须立刻处理的新线索。",
        "人物打开 <https://example.com> 核对公开记录。",
        1,
    )
    validate_card(_self_compose(markdown_autolink, fixture), 2)
    compact_hash_heading = _self_raw(2).replace(
        "  1. 人物核对现场痕迹。",
        "  1. #额外标题",
        1,
    )
    _expect_rejected(
        "compact hash marker in node",
        lambda: validate_card(_self_compose(compact_hash_heading, fixture), 2),
    )
    embedded_audit_title = _self_fixture()
    embedded_audit_title["title"] = "第九章 放行结论：四项检查通过"
    _expect_rejected(
        "embedded audit label in fixture title",
        lambda: _self_compose(_self_raw(2), embedded_audit_title),
    )

    wrong_case_id = _self_fixture()
    wrong_case_id["case_id"] = "02"
    _expect_rejected(
        "fixture case mismatch",
        lambda: _validate_fixture(wrong_case_id, "01"),
    )
    unfrozen_case = _self_fixture()
    unfrozen_case["case_id"] = "01"
    unfrozen_case["expected_scenes"] = 3
    _validate_fixture(unfrozen_case, "01")

    invalid_long_weight = _self_raw(2).replace(
        "场景1｜篇幅权重：短", "场景1｜篇幅权重：超长", 1
    )
    _expect_rejected(
        "weight longer than allowed",
        lambda: _self_compose(invalid_long_weight, fixture),
    )
    numeric_weight = _self_raw(2).replace(
        "场景1｜篇幅权重：短", "场景1｜篇幅权重：1500", 1
    )
    _expect_rejected(
        "numeric scene weight",
        lambda: _self_compose(numeric_weight, fixture),
    )
    legacy_budget_heading = _self_raw(2).replace(
        "场景1｜篇幅权重：短", "场景1｜建议字数：1500", 1
    )
    _expect_rejected(
        "legacy suggested-word heading",
        lambda: _self_compose(legacy_budget_heading, fixture),
    )
    legacy_required_field = _self_raw(2).replace(
        "- 视角偏压：", "- 必须呈现：", 1
    )
    _expect_rejected(
        "legacy required-presentation field",
        lambda: _self_compose(legacy_required_field, fixture),
    )
    neutral_viewpoint = _self_raw(2).replace(
        "- 视角偏压：人物更愿相信能够减轻自身责任的解释。",
        "- 视角偏压：无",
        1,
    )
    neutral_card = _self_compose(neutral_viewpoint, fixture)
    validate_card(neutral_card, 2)

    with tempfile.TemporaryDirectory() as temp_directory:
        temp_root = Path(temp_directory)
        valid_root = temp_root / "valid"
        valid_case = valid_root / "01"
        valid_case.mkdir(parents=True)
        for run in range(1, 6):
            (valid_case / f"run-{run}.txt").write_bytes(b"")
        if len(_require_five_case_outputs(valid_root, "01")) != 5:
            raise AssertionError("five expected raw files were not discovered")

        invalid_root = temp_root / "invalid"
        invalid_case = invalid_root / "01"
        invalid_case.mkdir(parents=True)
        for run in range(1, 6):
            (invalid_case / f"run-{run}.txt").write_bytes(b"")
        nested = invalid_case / "extra"
        nested.mkdir()
        (nested / "nested.txt").write_bytes(b"unexpected")
        _expect_rejected(
            "nested case file",
            lambda: _require_five_case_outputs(invalid_root, "01"),
        )

        release_record = _self_release_record("release-check schema sample")
        release_checks = {
            sample_key: dict(release_record)
            for sample_key in RELEASE_CHECK_KEYS
        }
        valid_release_json = temp_root / "release-valid.json"
        valid_release_json.write_bytes(
            json.dumps(release_checks, ensure_ascii=False, sort_keys=True).encode("utf-8")
        )
        if _release_checks_path(valid_release_json) != release_checks:
            raise AssertionError("valid release-check JSON did not round-trip")
        invalid_release_checks = dict(release_checks)
        invalid_release_checks.pop(sorted(RELEASE_CHECK_KEYS)[0])
        invalid_release_json = temp_root / "release-invalid.json"
        invalid_release_json.write_bytes(
            json.dumps(invalid_release_checks, ensure_ascii=False, sort_keys=True).encode("utf-8")
        )
        _expect_rejected(
            "release checks with missing top-level key",
            lambda: _release_checks_path(invalid_release_json),
        )

        def object_from_pairs(pairs):
            return "{" + ",".join(
                json.dumps(key, ensure_ascii=False) + ":" + value
                for key, value in pairs
            ) + "}"

        duplicate_sample = sorted(RELEASE_CHECK_KEYS)[0]
        release_pairs = [
            (
                sample_key,
                json.dumps(release_checks[sample_key], ensure_ascii=False, sort_keys=True),
            )
            for sample_key in sorted(RELEASE_CHECK_KEYS)
        ]
        release_pairs.append(
            (
                duplicate_sample,
                json.dumps(release_checks[duplicate_sample], ensure_ascii=False, sort_keys=True),
            )
        )
        duplicate_top_release = temp_root / "release-duplicate-top.json"
        duplicate_top_release.write_bytes(
            object_from_pairs(release_pairs).encode("utf-8")
        )
        _expect_rejected(
            "duplicate release sample key",
            lambda: _release_checks_path(duplicate_top_release),
        )

        duplicate_record_pairs = []
        for key, value in release_record.items():
            duplicate_record_pairs.append(
                (key, json.dumps(value, ensure_ascii=False))
            )
            if key == "新增重要事件":
                duplicate_record_pairs.append(
                    (key, json.dumps(value, ensure_ascii=False))
                )
        nested_release_pairs = []
        for sample_key in sorted(RELEASE_CHECK_KEYS):
            record_json = (
                object_from_pairs(duplicate_record_pairs)
                if sample_key == duplicate_sample
                else json.dumps(release_checks[sample_key], ensure_ascii=False, sort_keys=True)
            )
            nested_release_pairs.append((sample_key, record_json))
        duplicate_record_release = temp_root / "release-duplicate-record.json"
        duplicate_record_release.write_bytes(
            object_from_pairs(nested_release_pairs).encode("utf-8")
        )
        _expect_rejected(
            "duplicate key inside release record",
            lambda: _release_checks_path(duplicate_record_release),
        )

        duplicate_fixture = _self_fixture()
        duplicate_fixture["case_id"] = "01"
        fixture_pairs = []
        for key, value in duplicate_fixture.items():
            fixture_pairs.append((key, json.dumps(value, ensure_ascii=False)))
            if key == "title":
                fixture_pairs.append((key, json.dumps(value, ensure_ascii=False)))
        duplicate_fixture_root = temp_root / "fixtures-duplicate"
        duplicate_fixture_root.mkdir()
        (duplicate_fixture_root / "01.json").write_bytes(
            object_from_pairs(fixture_pairs).encode("utf-8")
        )
        _expect_rejected(
            "duplicate fixture key",
            lambda: _fixture_path(duplicate_fixture_root, "01"),
        )
    print("SELF_TEST_OK")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--emit-composed", nargs=2, metavar=("CASE_ID", "RUN_ID"))
    parser.add_argument("--validate-root", metavar="ROOT")
    parser.add_argument("--fixtures", metavar="ROOT")
    parser.add_argument(
        "--release-checks",
        metavar="RELEASE_JSON",
        help="JSON containing the exact 15 raw-output release records",
    )
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            if args.emit_composed or args.validate_root or args.release_checks:
                parser.error("--self-test cannot be combined with other commands")
            _self_test()
        elif args.emit_composed:
            if not args.validate_root:
                parser.error("--validate-root is required for --emit-composed")
            if not args.fixtures:
                parser.error("--fixtures is required for fixture-backed commands")
            if not args.release_checks:
                parser.error("--release-checks is required for --emit-composed")
            case_id, run_id = args.emit_composed
            fixture = _fixture_path(args.fixtures, case_id)
            _require_five_case_outputs(args.validate_root, case_id)
            output = _resolve_run(args.validate_root, case_id, run_id)
            release_checks = _release_checks_path(args.release_checks)
            raw = output.read_bytes()
            sample_key = fixture["case_id"] + "/" + output.name
            card = compose_card(raw, fixture, release_checks[sample_key])
            validate_card(card, fixture["expected_scenes"])
            print(card, end="")
        elif args.validate_root:
            if not args.fixtures:
                parser.error("--fixtures is required for fixture-backed commands")
            if not args.release_checks:
                parser.error("--release-checks is required for --validate-root")
            release_checks = _release_checks_path(args.release_checks)
            _validate_root(args.validate_root, args.fixtures, release_checks)
        else:
            parser.error("choose --self-test, --validate-root, or --emit-composed")
    except CardContractError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
