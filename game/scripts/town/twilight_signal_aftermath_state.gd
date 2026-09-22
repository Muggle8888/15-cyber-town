class_name TwilightSignalAftermathState
extends RefCounted

const SCHEMA_VERSION := 1
const EVENT_ID := "twilight_signal_aftermath_v1"
const NPC_IDS: Array[StringName] = [
	&"neon_guide",
	&"signal_archivist",
	&"night_courier",
]
const OUTCOME_IDS: Array[StringName] = [
	&"night_market_guide",
	&"archive_monitor",
	&"rain_route_beacon",
]
const ALL_STAGES: Array[StringName] = [
	&"locked",
	&"nia_briefing",
	&"consulting",
	&"decision_ready",
	&"aftermath",
	&"completed",
]
const OUTCOME_PROFILES := {
	&"night_market_guide": {
		"display_name": "夜市导引",
		"proposer": "Nia",
		"accent": "#f4a261",
		"secondary": "#ef7f9b",
		"sign": "夜市导引",
	},
	&"archive_monitor": {
		"display_name": "档案监听",
		"proposer": "Ivo",
		"accent": "#9a8cff",
		"secondary": "#73b9d8",
		"sign": "档案监听",
	},
	&"rain_route_beacon": {
		"display_name": "雨夜信标",
		"proposer": "Rhea",
		"accent": "#70d6c8",
		"secondary": "#79b8d8",
		"sign": "雨夜信标",
	},
}
const CONSULTATION_DRAFTS := {
	&"neon_guide": "暮光信号已经归档了。你觉得它以后应该怎样为街区工作？",
	&"signal_archivist": "如果保留这段暮光信号作为档案监听，它能为小镇留下什么？",
	&"night_courier": "如果把暮光信号作为雨夜信标，它能怎样帮助街道和投递？",
}
const REACTION_DRAFTS := {
	&"neon_guide": "我决定将暮光信号用于%s，你怎么看这个结果？",
	&"signal_archivist": "我决定将暮光信号用于%s，你会怎样记录这个结果？",
	&"night_courier": "我决定将暮光信号用于%s，这会怎样影响夜间路线？",
}

var stage: StringName = &"locked"
var consulted_npcs: Array[StringName] = []
var selected_outcome: StringName = &""
var reacted_npcs: Array[StringName] = []
var last_warning := ""
var _save_path := ""


func _init(save_path := "") -> void:
	_save_path = save_path


func load_or_initialize(prerequisite_completed: bool) -> String:
	last_warning = ""
	if _save_path.is_empty():
		_reset_without_save(prerequisite_completed)
		return ""
	if not FileAccess.file_exists(_save_path):
		_reset_without_save(prerequisite_completed)
		_save()
		return last_warning
	var file := FileAccess.open(_save_path, FileAccess.READ)
	if file == null:
		return _recover_from_invalid_save(
			"余波进度暂时无法读取，已恢复到可用起点。",
			prerequisite_completed,
		)
	var serialized := file.get_as_text()
	file.close()
	var parser := JSON.new()
	if parser.parse(serialized) != OK or not _load_valid_payload(parser.data):
		return _recover_from_invalid_save(
			"余波进度文件无效，已恢复到可用起点。",
			prerequisite_completed,
		)
	if stage == &"locked" and prerequisite_completed:
		unlock_if_ready(true)
	return last_warning


func unlock_if_ready(prerequisite_completed: bool) -> bool:
	if not prerequisite_completed or stage != &"locked":
		return false
	stage = &"nia_briefing"
	last_warning = ""
	_save()
	return true


func current_profile() -> Dictionary:
	match stage:
		&"locked":
			return {
				"kind": &"locked",
				"progress": 0,
				"objective": "先完成暮光失联信号",
			}
		&"nia_briefing":
			return {
				"kind": &"dialogue",
				"progress": 1,
				"objective": "与 Nia 商量暮光信号的新用途",
			}
		&"consulting":
			return {
				"kind": &"dialogue",
				"progress": 1 + maxi(0, consulted_npcs.size() - 1),
				"objective": "听取 Ivo 与 Rhea 的方案（%d/2）" % maxi(
					0,
					consulted_npcs.size() - 1,
				),
			}
		&"decision_ready":
			return {
				"kind": &"choice",
				"target_id": &"signal_calibration_station",
				"progress": 4,
				"objective": "三方意见齐全 · 在校准台作出选择",
			}
		&"aftermath":
			return {
				"kind": &"dialogue",
				"progress": 4 + reacted_npcs.size(),
				"objective": "回访三名 NPC（%d/3）" % reacted_npcs.size(),
			}
		&"completed":
			return {
				"kind": &"completed",
				"progress": 7,
				"objective": "%s已成为暮光信号的新用途" % outcome_display_name(),
			}
	return {}


func dialogue_action_for(npc_id: StringName) -> Dictionary:
	if npc_id not in NPC_IDS:
		return {}
	if stage == &"nia_briefing" and npc_id == &"neon_guide":
		return {
			"phase": &"consultation",
			"draft": String(CONSULTATION_DRAFTS[npc_id]),
		}
	if (
		stage == &"consulting"
		and npc_id in [&"signal_archivist", &"night_courier"]
		and npc_id not in consulted_npcs
	):
		return {
			"phase": &"consultation",
			"draft": String(CONSULTATION_DRAFTS[npc_id]),
		}
	if stage == &"aftermath" and npc_id not in reacted_npcs:
		return {
			"phase": &"reaction",
			"draft": String(REACTION_DRAFTS[npc_id]) % outcome_display_name(),
		}
	return {}


func record_dialogue(npc_id: StringName, phase: StringName, status: String) -> bool:
	if status != "completed":
		return false
	var action := dialogue_action_for(npc_id)
	if action.is_empty() or StringName(action.get("phase", &"")) != phase:
		return false
	if phase == &"consultation":
		consulted_npcs.append(npc_id)
		if stage == &"nia_briefing":
			stage = &"consulting"
		elif consulted_npcs.size() == NPC_IDS.size():
			stage = &"decision_ready"
	elif phase == &"reaction":
		reacted_npcs.append(npc_id)
		if reacted_npcs.size() == NPC_IDS.size():
			stage = &"completed"
	else:
		return false
	last_warning = ""
	_save()
	return true


func choose_outcome(outcome_id: StringName) -> bool:
	if stage != &"decision_ready" or outcome_id not in OUTCOME_IDS:
		return false
	selected_outcome = outcome_id
	reacted_npcs = []
	stage = &"aftermath"
	last_warning = ""
	_save()
	return true


func reset_event(prerequisite_completed: bool) -> bool:
	last_warning = ""
	_reset_without_save(prerequisite_completed)
	return _save()


func is_completed() -> bool:
	return stage == &"completed"


func outcome_display_name() -> String:
	var profile := outcome_profile()
	return String(profile.get("display_name", "暮光信号"))


func outcome_profile() -> Dictionary:
	return (OUTCOME_PROFILES.get(selected_outcome, {}) as Dictionary).duplicate(true)


func save_path_for_testing() -> String:
	return _save_path


func _reset_without_save(prerequisite_completed: bool) -> void:
	stage = &"nia_briefing" if prerequisite_completed else &"locked"
	consulted_npcs = []
	selected_outcome = &""
	reacted_npcs = []


func _recover_from_invalid_save(message: String, prerequisite_completed: bool) -> String:
	_reset_without_save(prerequisite_completed)
	last_warning = message
	_save()
	return last_warning


func _load_valid_payload(parsed: Variant) -> bool:
	if typeof(parsed) != TYPE_DICTIONARY:
		return false
	var payload: Dictionary = parsed
	var keys := [
		"schema_version",
		"event_id",
		"stage",
		"consulted_npcs",
		"selected_outcome",
		"reacted_npcs",
		"completed",
	]
	if payload.size() != keys.size():
		return false
	for key: String in keys:
		if not payload.has(key):
			return false
	if (
		typeof(payload["schema_version"]) not in [TYPE_FLOAT, TYPE_INT]
		or int(payload["schema_version"]) != SCHEMA_VERSION
	):
		return false
	if typeof(payload["event_id"]) != TYPE_STRING or String(payload["event_id"]) != EVENT_ID:
		return false
	if typeof(payload["stage"]) != TYPE_STRING:
		return false
	var loaded_stage := StringName(payload["stage"])
	if loaded_stage not in ALL_STAGES:
		return false
	if (
		typeof(payload["selected_outcome"]) != TYPE_STRING
		or typeof(payload["completed"]) != TYPE_BOOL
	):
		return false
	var loaded_consulted: Variant = _validated_npc_array(payload["consulted_npcs"])
	var loaded_reacted: Variant = _validated_npc_array(payload["reacted_npcs"])
	if loaded_consulted == null or loaded_reacted == null:
		return false
	var loaded_outcome := StringName(payload["selected_outcome"])
	if not loaded_outcome.is_empty() and loaded_outcome not in OUTCOME_IDS:
		return false
	if not _combination_is_valid(
		loaded_stage,
		loaded_consulted,
		loaded_outcome,
		loaded_reacted,
		bool(payload["completed"]),
	):
		return false
	stage = loaded_stage
	consulted_npcs.assign(loaded_consulted)
	selected_outcome = loaded_outcome
	reacted_npcs.assign(loaded_reacted)
	return true


func _validated_npc_array(value: Variant) -> Variant:
	if typeof(value) != TYPE_ARRAY:
		return null
	var result: Array[StringName] = []
	for raw_npc: Variant in value:
		if typeof(raw_npc) != TYPE_STRING:
			return null
		var npc_id := StringName(raw_npc)
		if npc_id not in NPC_IDS or npc_id in result:
			return null
		result.append(npc_id)
	return result


func _combination_is_valid(
	loaded_stage: StringName,
	loaded_consulted: Array,
	loaded_outcome: StringName,
	loaded_reacted: Array,
	loaded_completed: bool,
) -> bool:
	if loaded_completed != (loaded_stage == &"completed"):
		return false
	match loaded_stage:
		&"locked", &"nia_briefing":
			return (
				loaded_consulted.is_empty()
				and loaded_outcome.is_empty()
				and loaded_reacted.is_empty()
			)
		&"consulting":
			return (
				&"neon_guide" in loaded_consulted
				and loaded_consulted.size() in [1, 2]
				and loaded_outcome.is_empty()
				and loaded_reacted.is_empty()
			)
		&"decision_ready":
			return (
				_has_all_npcs(loaded_consulted)
				and loaded_outcome.is_empty()
				and loaded_reacted.is_empty()
			)
		&"aftermath":
			return (
				_has_all_npcs(loaded_consulted)
				and loaded_outcome in OUTCOME_IDS
				and loaded_reacted.size() < NPC_IDS.size()
			)
		&"completed":
			return (
				_has_all_npcs(loaded_consulted)
				and loaded_outcome in OUTCOME_IDS
				and _has_all_npcs(loaded_reacted)
			)
	return false


func _has_all_npcs(values: Array) -> bool:
	if values.size() != NPC_IDS.size():
		return false
	for npc_id: StringName in NPC_IDS:
		if npc_id not in values:
			return false
	return true


func _save() -> bool:
	if _save_path.is_empty():
		return true
	var file := FileAccess.open(_save_path, FileAccess.WRITE)
	if file == null:
		last_warning = "余波进度暂时无法保存，本次仍可继续。"
		return false
	var consulted: Array[String] = []
	for npc_id: StringName in consulted_npcs:
		consulted.append(String(npc_id))
	var reacted: Array[String] = []
	for npc_id: StringName in reacted_npcs:
		reacted.append(String(npc_id))
	file.store_string(
		JSON.stringify(
			{
				"schema_version": SCHEMA_VERSION,
				"event_id": EVENT_ID,
				"stage": String(stage),
				"consulted_npcs": consulted,
				"selected_outcome": String(selected_outcome),
				"reacted_npcs": reacted,
				"completed": is_completed(),
			},
			"  ",
		)
	)
	file.close()
	return true
