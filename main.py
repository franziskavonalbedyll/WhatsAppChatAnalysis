# -*- coding: utf-8 -*-
"""
Simple script to analyze and visualize WhatsApp Chats.

@author: FvA
"""
import collections
import itertools
import re

import numpy as np
import pandas as pd
import seaborn as sns


def compute_word_usage_frequency(message_column: pd.core.series.Series) -> collections.Counter:
    """
    This function computes how often each word occured in the given dataframe column.

    Parameters
    ----------
    message_column : pd.core.series.Series
        Dataframe column.

    Returns
    -------
    TYPE
        Counter object of word occurences

    """
    words = [message.split() for message in message_column]
    words = [val for sublist in words for val in sublist]  # flatten nested list
    return collections.Counter(words)


def main():
    sns.set_theme()
    plot = True
    response_timelimit = 6  # defines how many hours can pass before a response will not be used anymore to calculate
    # the average response time

    # Set Up
    # Read in WhatsApp chat data
    fpath = r'data/chats.txt'
    with open(fpath, encoding="UTF-8") as f:
        lines = f.readlines()

    # collect data for dataframe
    pattern = "(\[(?P<datetime>\d{2}.\d{2}.\d{2}, \d{2}:\d{2}:\d{2})] (?P<messenger>[^:]*): )?((?P<message>.*))"
    data = [re.search(pattern, line).groupdict() for line in lines]

    # create dataframe
    df = pd.DataFrame(data)
    df = df[df["message"] != ""]  # remove empty messages

    # transform date and time to datetime format
    df["datetime"] = pd.to_datetime(df["datetime"], format="%d.%m.%y, %H:%M:%S")
    df["date"] = df["datetime"].dt.date
    df["time"] = df["datetime"].dt.time

    # take care of multiline messages
    df = df.fillna(method="ffill")  # use time and messenger info from preciding line for multiline messages

    # calculate response times between messages of different messengers
    df_response_times = df[df["messenger"] != df["messenger"].shift(1)]
    df_response_times["response_time"] = df_response_times["datetime"].diff()
    df_response_times = df_response_times[
        df_response_times["response_time"] <= pd.Timedelta(response_timelimit, unit="h")]
    df = pd.merge(df, df_response_times, how="outer")

    # Analysis
    messengers = set(df["messenger"])

    # averages
    average_response_times = {messenger: df[df["messenger"] == messenger]["response_time"].mean() for messenger in
                              messengers}
    average_message_length = {messenger: round(np.mean(list(map(len, df[df["messenger"] == messenger]["message"])))) for
                              messenger in messengers}
    average_messages_per_day = {messenger: (len(df[df["messenger"] == messenger])) / len(set(df["date"])) for messenger
                                in messengers}
    messages_ratio = {
        f"{messenger_1} vs {messenger_2}": average_messages_per_day[messenger_1] / average_messages_per_day[messenger_2]
        for messenger_1, messenger_2 in itertools.combinations(messengers, 2)}

    # save averages to df
    df_averages = pd.DataFrame(
        [average_response_times, average_message_length, average_messages_per_day],
        index=["Average Response Time", "Average Message Length", "Average amount of messages per day"])
    df_averages.to_csv(r"out/results.csv")

    word_usage_frequency = {messenger: compute_word_usage_frequency(df[df["messenger"] == messenger]["message"]) for
                            messenger in messengers}

    # Plots
    if plot:
        # Plot messages over the day
        times_counted = pd.DataFrame(
            {messenger: (df[df["messenger"] == messenger]["datetime"].dt.round("H").dt.hour.value_counts())
             for messenger in messengers})

        abs_messages_per_hour_plt = times_counted.plot()
        abs_messages_per_hour_plt.set(xticks=np.arange(0, 25, 2), xlabel="Time rounded to the nearest hour",
                                      ylabel="Amount of messages sent")
        abs_messages_per_hour_plt.figure.savefig(r"out/abs_messages_per_hour_plt.png")

        avg_messages_per_hour = times_counted / len(set(df["date"]))
        avg_messages_per_hour_plt = avg_messages_per_hour.plot()
        avg_messages_per_hour_plt.set(xticks=np.arange(0, 25, 2), xlabel="Time rounded to the nearest hour",
                                     ylabel="Average amount of messages sent")
        avg_messages_per_hour_plt.figure.savefig(r"out/avg_messages_per_hour_plt.png")

        # Plot messages over the year
        days_counted = pd.DataFrame(
            {messenger: df[df["messenger"] == messenger]["datetime"].dt.date.value_counts() for messenger in
             messengers})
        abs_messages_over_the_year_plt = pd.DataFrame(days_counted).plot()
        abs_messages_over_the_year_plt.figure.savefig(r"out/abs_messages_over_the_year_plt.png")


if __name__ == "__main__":
    main()
