class_name TwilightSignalEventState
extends RefCounted

const SCHEMA_VERSION := 1
const EVENT_ID := "twilight_lost_signal_v1"
const ACTIVE_STAGES: Array[StringName] = [
	&"nia_intro",
	&"guide_clue",
	&"ivo_analysis",
	&"signal_clue",
	&"rhea_route",
	&"delivery_clue",
	&"nia_conclusion",
]
const ALL_STAGES: Array[StringName] = [
	&"not_started",
	&"nia_intro",
	&"guide_clue",
	&"ivo_analysis",
	&"signal_clue",
	&"rhea_route",
	&"delivery_clue",
	&"nia_conclusion",
	&"completed",
]
const CLUE_IDS: Array[StringName] = [
	&"twilight_guide_board",
	&"signal_calibration_station",
	&"rain_delivery_board",
]
const STEP_PROFILES := {
	&"nia_intro": {
		"kind": &"dialogue",
		"target_id": &"neon_guide",
		"progress": 1,
		"objective": "和 Nia 聊聊今晚异常的灯光",
		"draft": "今晚的夜市灯带似乎少了一段光，你注意到了吗？",
	},
	&"guide_clue": {
		"kind": &"landmark",
		"target_id": &"twilight_guide_board",
		"progress": 2,
		"objective": "调查暮光导览牌",
	},
	&"ivo_analysis": {
		"kind": &"dialogue",
		"target_id": &"signal_archivist",
		"progress": 3,
		"objective": "请 Ivo 核对导览牌上的旧广播编号",
		"draft": "我在暮光导览牌发现一段异常灯带标记，它和旧广播编号有关吗？",
	},
	&"signal_clue": {
		"kind": &"landmark",
		"target_id": &"signal_calibration_station",
		"progress": 4,
		"objective": "调查信号校准台",
	},
	&"rhea_route": {
		"kind": &"dialogue",
		"target_id": &"night_courier",
		"progress": 5,
		"objective": "请 Rhea 核对广播编号与雨夜路线",
		"draft": "Ivo 发现旧广播编号可能对应雨夜路线，这条路线现在如何核对？",
	},
	&"delivery_clue": {
		"kind": &"landmark",
		"target_id": &"rain_delivery_board",
		"progress": 6,
		"objective": "调查雨棚投递板",
	},
	&"nia_conclusion": {
		"kind": &"dialogue",
		"target_id": &"neon_guide",
		"progress": 7,
		"objective": "返回 Nia，归档暮光信号",
		"draft": "我们核对了旧广播编号和雨夜路线，这段暮光信号应该怎样记录？",
	},
}
const NEXT_STAGE := {
	&"nia_intro": &"guide_clue",
	&"guide_clue": &"ivo_analysis",
	&"ivo_analysis": &"signal_clue",
	&"signal_clue": &"rhea_route",
	&"rhea_route": &"delivery_clue",
	&"delivery_clue": &"nia_conclusion",
	&"nia_conclusion": &"completed",
}
const EXPECTED_CLUES := {
	&"not_started": [],
	&"nia_intro": [],
	&"guide_clue": [],
	&"ivo_analysis": [&"twilight_guide_board"],
	&"signal_clue": [&"twilight_guide_board"],
	&"rhea_route": [&"twilight_guide_board", &"signal_calibration_station"],
	&"delivery_clue": [&"twilight_guide_board", &"signal_calibration_station"],
	&"nia_conclusion": CLUE_IDS,
	&"completed": CLUE_IDS,
}

var stage: StringName = &"not_started"
var recorded_clues: Array[StringName] = []
var last_warning := ""
var _save_path := ""


func _init(save_path := "") -> void:
	_save_path = save_path


func load_or_start() -> String:
	last_warning = ""
	if _save_path.is_empty():
		_start_without_save()
		return ""
	if not FileAccess.file_exists(_save_path):
		_start_without_save()
		_save()
		return last_warning
	var file := FileAccess.open(_save_path, FileAccess.READ)
	if file == null:
		return _recover_from_invalid_save("事件进度暂时无法读取，已从头开始。")
	var serialized := file.get_as_text()
	file.close()
	var parser := JSON.new()
	if parser.parse(serialized) != OK:
		return _recover_from_invalid_save("事件进度文件无效，已从头开始。")
	var parsed: Variant = parser.data
	if not _load_valid_payload(parsed):
		return _recover_from_invalid_save("事件进度文件无效，已从头开始。")
	if stage == &"not_started":
		_start_without_save()
		_save()
	return last_warning


func current_profile() -> Dictionary:
	if stage == &"completed":
		return {
			"kind": &"completed",
			"target_id": &"",
			"progress": 7,
			"objective": "暮光信号已归档",
		}
	return (STEP_PROFILES.get(stage, {}) as Dictionary).duplicate(true)


func is_completed() -> bool:
	return stage == &"completed"


func advance_dialogue(npc_id: StringName, status: String) -> bool:
	var profile := current_profile()
	if (
		status != "completed"
		or StringName(profile.get("kind", &"")) != &"dialogue"
		or StringName(profile.get("target_id", &"")) != npc_id
	):
		return false
	return _advance()


func record_landmark(landmark_id: StringName) -> bool:
	var profile := current_profile()
	if (
		StringName(profile.get("kind", &"")) != &"landmark"
		or StringName(profile.get("target_id", &"")) != landmark_id
	):
		return false
	if landmark_id not in recorded_clues:
		recorded_clues.append(landmark_id)
	return _advance()


func reset_event() -> bool:
	last_warning = ""
	_start_without_save()
	return _save()


func clear_warning() -> void:
	last_warning = ""


func save_path_for_testing() -> String:
	return _save_path


func _advance() -> bool:
	if not NEXT_STAGE.has(stage):
		return false
	stage = StringName(NEXT_STAGE[stage])
	last_warning = ""
	_save()
	return true


func _start_without_save() -> void:
	stage = &"nia_intro"
	recorded_clues = []


func _recover_from_invalid_save(message: String) -> String:
	_start_without_save()
	last_warning = message
	_save()
	return last_warning


func _load_valid_payload(parsed: Variant) -> bool:
	if typeof(parsed) != TYPE_DICTIONARY:
		return false
	var payload: Dictionary = parsed
	if payload.size() != 5:
		return false
	for key: String in ["schema_version", "event_id", "stage", "recorded_clues", "completed"]:
		if not payload.has(key):
			return false
	if (
		typeof(payload["schema_version"]) != TYPE_FLOAT
		and typeof(payload["schema_version"]) != TYPE_INT
	):
		return false
	if int(payload["schema_version"]) != SCHEMA_VERSION:
		return false
	if typeof(payload["event_id"]) != TYPE_STRING or String(payload["event_id"]) != EVENT_ID:
		return false
	if typeof(payload["stage"]) != TYPE_STRING:
		return false
	var loaded_stage := StringName(payload["stage"])
	if loaded_stage not in ALL_STAGES:
		return false
	if typeof(payload["completed"]) != TYPE_BOOL:
		return false
	if bool(payload["completed"]) != (loaded_stage == &"completed"):
		return false
	if typeof(payload["recorded_clues"]) != TYPE_ARRAY:
		return false
	var loaded_clues: Array[StringName] = []
	for clue: Variant in payload["recorded_clues"]:
		if typeof(clue) != TYPE_STRING:
			return false
		var clue_id := StringName(clue)
		if clue_id not in CLUE_IDS or clue_id in loaded_clues:
			return false
		loaded_clues.append(clue_id)
	var expected: Array = EXPECTED_CLUES[loaded_stage]
	if loaded_clues.size() != expected.size():
		return false
	for clue_id: StringName in expected:
		if clue_id not in loaded_clues:
			return false
	stage = loaded_stage
	recorded_clues = loaded_clues
	return true


func _save() -> bool:
	if _save_path.is_empty():
		return true
	var file := FileAccess.open(_save_path, FileAccess.WRITE)
	if file == null:
		last_warning = "事件进度暂时无法保存，本次仍可继续。"
		return false
	var clues: Array[String] = []
	for clue_id: StringName in recorded_clues:
		clues.append(String(clue_id))
	file.store_string(
		JSON.stringify(
			{
				"schema_version": SCHEMA_VERSION,
				"event_id": EVENT_ID,
				"stage": String(stage),
				"recorded_clues": clues,
				"completed": is_completed(),
			},
			"  ",
		)
	)
	file.close()
	return true
