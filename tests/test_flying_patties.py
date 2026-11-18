from flying_patties import FlyingPatties


def test_spawn_zero_count_creates_nothing():
    patties = FlyingPatties()
    patties.spawn(start=(0, 0), target=(100, 100), count=0, now=0.0)
    assert patties._patties == []


def test_spawned_patty_starts_at_start_and_ends_at_target():
    patties = FlyingPatties()
    patties.spawn(start=(10, 500), target=(480, 40), count=1, now=0.0)
    patty = patties._patties[0]
    assert patty.position(now=0.0) == (10, 500)
    assert patty.position(now=patty.spawn_time + patty.duration) == (480, 40)


def test_update_removes_finished_patties():
    patties = FlyingPatties()
    patties.spawn(start=(0, 0), target=(10, 10), count=1, now=0.0)
    patties.update(now=0.0)
    assert len(patties._patties) == 1
    patties.update(now=10.0)  # long past the 0.6s duration
    assert patties._patties == []


def test_staggered_spawns_launch_one_after_another():
    patties = FlyingPatties()
    patties.spawn(start=(0, 0), target=(10, 10), count=3, now=0.0)
    spawn_times = sorted(p.spawn_time for p in patties._patties)
    assert spawn_times[0] == 0.0
    assert spawn_times[1] > spawn_times[0]
    assert spawn_times[2] > spawn_times[1]


if __name__ == "__main__":
    test_spawn_zero_count_creates_nothing()
    test_spawned_patty_starts_at_start_and_ends_at_target()
    test_update_removes_finished_patties()
    test_staggered_spawns_launch_one_after_another()
    print("OK")
