from datetime import timedelta


def time_generator(start_time):
    """
    генератор времени, который повышает текущее время на 1 секунду при каждом вызове
    """
    current_time = start_time
    while True:
        yield current_time
        current_time += timedelta(seconds=1)
