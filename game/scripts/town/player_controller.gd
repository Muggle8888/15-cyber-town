class_name TownPlayerController
extends CharacterBody2D

@export_range(1.0, 300.0, 1.0) var move_speed := 92.0

@onready var _sprite: Sprite2D = $Sprite2D

var movement_locked := false
var _animation_elapsed := 0.0
var _facing_row := 0


func _physics_process(delta: float) -> void:
	var direction := Vector2.ZERO
	if not movement_locked:
		direction = Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = direction * move_speed
	move_and_slide()
	_update_animation(direction, delta)


func set_movement_locked(locked: bool) -> void:
	movement_locked = locked
	if locked:
		velocity = Vector2.ZERO


func normalized_velocity_for_input(raw_direction: Vector2) -> Vector2:
	if raw_direction.length_squared() > 1.0:
		raw_direction = raw_direction.normalized()
	return raw_direction * move_speed


func _update_animation(direction: Vector2, delta: float) -> void:
	if direction != Vector2.ZERO:
		if absf(direction.x) > absf(direction.y):
			_facing_row = 3 if direction.x > 0.0 else 2
		else:
			_facing_row = 0 if direction.y > 0.0 else 1
		_animation_elapsed += delta
		_sprite.frame_coords = Vector2i(1 + int(_animation_elapsed * 8.0) % 2, _facing_row)
	else:
		_animation_elapsed = 0.0
		_sprite.frame_coords = Vector2i(0, _facing_row)
