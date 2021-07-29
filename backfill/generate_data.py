import random
import datetime
import time
import os

number_of_days_to_generate = 7

def format_metric(name, pr_id, repo_name, value, timestamp):
    label = 'instance="gateway.docker.internal:8000",job="compass_exporter",pr_id="'
    label = label + pr_id + '",repo_name="' + repo_name + '"'
    return "%s{%s} %f %d" % (name, label, value, timestamp)


def print_file(out_data):
    output = []
    output.append("# HELP pr_age PR Age matrics")
    output.append("# TYPE pr_age gauge")
    output = output + out_data
    output.append("# EOF")

    print('\n'.join(output))


today = datetime.date.fromtimestamp(time.time())
start_date = today - datetime.timedelta(days=number_of_days_to_generate)

data = []
repo_pr_dict = {
    "beecash-api" : {
        "max_pr"        : 16,
        "min_avg_pr"    : 25000},
    "compass" : {
        "max_pr"        : 3,
        "min_avg_pr"    : 12000},
    "monaco" : {
        "max_pr"        : 4,
        "min_avg_pr"    : 17000},
    "react-native-otp-input" : {
        "max_pr"        : 3,
        "min_avg_pr"    : 45000},
    "react-native-bluetooth-escpos-printer" : {
        "max_pr"        : 2,
        "min_avg_pr"    : 41000}
}

unixtime = time.mktime(start_date.timetuple())
resolution_sec = 60

flag = 0
for i in range(number_of_days_to_generate):
    for n in range(int(86400/resolution_sec)):
        for repo, value in repo_pr_dict.items():
            pr_count = random.randint(1, value["max_pr"])
            for cur_pr in range(1, pr_count + 1):
                value["min_avg_pr"] = value["min_avg_pr"] + 1
                data.append(format_metric("pr_age", str(cur_pr), repo, float(value["min_avg_pr"]), unixtime))

        unixtime += resolution_sec


print_file(data)