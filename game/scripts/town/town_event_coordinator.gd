class_name TownEventCoordinator
extends RefCounted

const LOST_SIGNAL_ID := &"twilight_lost_signal_v1"
const AFTERMATH_ID := &"twilight_signal_aftermath_v1"

var lost_signal: TwilightSignalEventState
var aftermath: TwilightSignalAftermathState


func _init(
	lost_signal_state: TwilightSignalEventState,
	aftermath_state: TwilightSignalAftermathState,
) -> void:
	lost_signal = lost_signal_state
	aftermath = aftermath_state


func synchronize() -> bool:
	return aftermath.unlock_if_ready(lost_signal.is_completed())


func active_event_id() -> StringName:
	return AFTERMATH_ID if lost_signal.is_completed() else LOST_SIGNAL_ID


func current_profile() -> Dictionary:
	if active_event_id() == AFTERMATH_ID:
		return aftermath.current_profile()
	return lost_signal.current_profile()


func active_is_completed() -> bool:
	if active_event_id() == AFTERMATH_ID:
		return aftermath.is_completed()
	return lost_signal.is_completed()
