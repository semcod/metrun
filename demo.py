from metrun import trace, get_records, analyse, print_report

@trace
def slow_query(n):
    return sum(i * i for i in range(n))

@trace
def handler(items):
    return [slow_query(i) for i in items]

if __name__ == "__main__":
    handler(list(range(100)))
    bottlenecks = analyse(get_records())
    print_report(bottlenecks)
