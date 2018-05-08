import os
import json

def get_throughput_for_file(file):
    json_file = json.load(file)
    throughput = json_file["end"]["sum_received"]["bits_per_second"]
    return throughput

def compute_average_for_run(test_number, test_type):
    dirname = "test_" + str(test_number) + "_" + test_type
    throughput_sum = 0
    throughput_count = 0
    for filename in os.listdir(dirname):
        fd = open(dirname + "/" + filename, 'r')
        throughput_sum += get_throughput_for_file(fd)
        throughput_count += 1
    return throughput_sum / throughput_count

def compute_average_test(num_tests, test_type):
    cur_sum = 0
    for i in range(num_tests):
        cur_sum += compute_average_for_run(i, test_type)
    return cur_sum / num_tests

def compute_average_all_tests(num_tests):
    results = {}
    results['ksp'] = compute_average_test(num_tests, "KSP")
    #results['ksp_8'] = compute_average_test(num_tests, "KSP_8")
    #results['ecmp'] = compute_average_test(num_tests, "ECMP")
    #results['ecmp_8'] = compute_average_test(num_tests, "ECMP_8")
    return results

if __name__ == "__main__":
    results = compute_average_all_tests(1)
    for k in results:
        print k, results[k]
