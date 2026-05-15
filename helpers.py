def calc_received(payment_1, payment_2, payment_3):
    return (payment_1 or 0) + (payment_2 or 0) + (payment_3 or 0)


def calc_pending(total_booking, payment_1, payment_2, payment_3):
    return total_booking - calc_received(payment_1, payment_2, payment_3)


def calc_status(pending, payment_1, payment_2, payment_3):
    if pending <= 0:
        return 'Paid'
    if calc_received(payment_1, payment_2, payment_3) > 0:
        return 'Partial'
    return 'Unpaid'
