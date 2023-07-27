import sys
import collections

TestResult = collections.namedtuple('TestResult', ['is_topic', 'content', 'passed'])


def is_valid_test_result(s: str):
    return 'Info: test:' in s or ('Info:' in s and ('[ PASSED ]' in s or '[ FAILED ]' in s))


def parse_test_result(s: str):
    if 'Info: test:' in s:
        test_topic = s.split('Info: test:')[1].strip()
        return TestResult(True, test_topic, None)
    else:
        detail = s.split('Info:')[1].replace('[ PASSED ]', '').replace('[ FAILED ]', '').strip().rstrip('.')
        return TestResult(False, detail, '[ PASSED ]' in s)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: report.py /path/to/staging_result /path/to/pr_result')
        exit(1)
    staging_result_path = sys.argv[1]
    pr_result_path = sys.argv[2]

    with open(staging_result_path, errors='ignore') as reader:
        staging_results = list(map(parse_test_result, filter(is_valid_test_result, reader.readlines())))

    with open(pr_result_path, errors='ignore') as reader:
        pr_results = list(map(parse_test_result, filter(is_valid_test_result, reader.readlines())))

    if len(staging_results) != len(pr_results):
        print(
            'Error: Failed to match test results.\n'
            'Code in this PR can only run {} tests, while staging branch has {} ones.\n'
            'See the detailed logs below:\n'
            '{}'
            .format(
                len(pr_results),
                len(staging_results),
                open(pr_result_path, errors='ignore').read()
            ),
        )
        exit(1)

    test_passed = True

    last_topic = None
    broken_tests = []
    fixed_tests = []

    for i in range(len(staging_results)):
        if staging_results[i].is_topic:
            last_topic = staging_results[i].content
            continue

        staging_passed = staging_results[i].passed
        pr_passed = pr_results[i].passed

        if staging_passed and not pr_passed:
            broken_tests.append((last_topic, staging_results[i].content))
            test_passed = False
        elif pr_passed and not staging_passed:
            fixed_tests.append((last_topic, staging_results[i].content))

    passed_tests_count = len(list(filter(lambda x: not x.is_topic and x.passed, pr_results)))
    all_tests_count = len(list(filter(lambda x: not x.is_topic, pr_results)))
    print(
        '=========== Test Report ===========\n'
        '{} tests are broken in your pull request:\n'
        '{}\n'
        '\n'
        '{} tests are newly fixed:\n'
        '{}\n'
        '\n'
        'Statics: passed {}/{} libc tests ({:.2f}%)'
        .format(
            len(broken_tests),
            '\n'.join(['{}: {}'.format(topic, content) for topic, content in broken_tests]),
            len(fixed_tests),
            '\n'.join(['{}: {}'.format(topic, content) for topic, content in fixed_tests]),
            passed_tests_count,
            all_tests_count,
            passed_tests_count / all_tests_count * 100
        )
    )

    exit(0 if test_passed else 1)
