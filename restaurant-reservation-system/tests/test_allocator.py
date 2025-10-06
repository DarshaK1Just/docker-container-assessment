from datetime import datetime, timedelta
from reservation_system.allocator import find_combinations_for_party




def test_find_single_table():
    tables = [{'id':1,'capacity':2},{'id':2,'capacity':4},{'id':3,'capacity':6}]
    combo = find_combinations_for_party(tables, 4)
    assert combo == [2]




def test_find_combo():
    tables = [{'id':1,'capacity':2},{'id':2,'capacity':2},{'id':3,'capacity':4}]
    combo = find_combinations_for_party(tables, 4)
    # prefer single table of capacity 4
    assert combo == [3]




def test_find_combined_small():
    tables = [{'id':1,'capacity':2},{'id':2,'capacity':2},{'id':3,'capacity':2}]
    combo = find_combinations_for_party(tables, 5, max_tables_to_combine=3)
    # 2+2+2 =6 should satisfy
    assert set(combo) == {1,2,3}