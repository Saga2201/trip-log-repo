from helpers import calc_pending, calc_received, calc_status


def test_calc_received_sums_all_payments():
    assert calc_received(10000, 5000, 3000) == 18000


def test_calc_received_treats_none_as_zero():
    assert calc_received(None, 5000, None) == 5000


def test_calc_pending_full_payment():
    assert calc_pending(18000, 10000, 5000, 3000) == 0


def test_calc_pending_partial_payment():
    assert calc_pending(32000, 20000, 0, 0) == 12000


def test_calc_pending_no_payment():
    assert calc_pending(12500, 0, 0, 0) == 12500


def test_calc_status_paid():
    assert calc_status(0, 10000, 5000, 3000) == 'Paid'


def test_calc_status_partial():
    assert calc_status(12000, 20000, 0, 0) == 'Partial'


def test_calc_status_unpaid():
    assert calc_status(12500, 0, 0, 0) == 'Unpaid'
