import numpy as np
import pandas as pd
import scipy.io
import os
os.environ["CDF_LIB"] = "C:/Users/bella/Desktop/cdf3.8.0_64bit_VS2015/lib"
from spacepy import pycdf
from datetime import datetime, timedelta
from pyspedas import time_string
from pyspedas.utilities.interpol import interpol
from pyspedas.utilities.data_exists import data_exists
from pyspedas.utilities.download import download
from math import floor
from scipy.interpolate import interp1d
from datetime import *

def get_time(begin_time):
    if le4 < begin_time < 1e5:
        hour = '0' + str(int(begin_time // 1e4))
    elif begin_time < 1e4:
        hour = '00'
    else:
        hour = str(int(begin_time // 1e4))

    minute = int((begin_time % 1e4) // 1e2)
    if minute < 10:
        minute = '0' + str(minute)
    else:
        minute = str(minute)

    second = int((begin_time % 1e5) % 100)
    if second < 10:
        second = '0' + str(second)
    else:
        second = str(second)

    time = hour + ':' + minute + ':' + second + '.0'

    temp_hour = int(int(hour) / 6) * 6
    if temp_hour < 10:
        data_hour = '0' + str(temp_hour)
    else:
        data_hour = str(temp_hour)

    return time, data_hour


def get_theta(data):
    norm_data = np.sqrt(data[:, 0] ** 2 + data[:, 1] ** 2 + data[:, 2] ** 2)
    theta = np.arccos(data[:, 0] / norm_data)
    return np.degrees(theta)


def get_norm(data):
    result = np.sqrt(data[:, 0] ** 2 + data[:, 1] ** 2 + data[:, 2] ** 2)
    return result

def get_kink_events(theta, time_length, abs_B):
    # 设置delta theta和kink事件持续时间的阈值
    theta_threshold = 15  # 单位：度
    theta_threshold_of_kink_min = 25  # 单位：度
    theta_threshold_of_kink_max = 180  # 单位：度
    exist_time_threshold = 60  # 单位：秒
    step_time_threshold = 60  # 单位：秒

    # 获取theta的前50%值作为theta的基准值
    p = 50
    theta_base = np.percentile(theta, p)
    sig = 0
    if theta_base < 50:
        sig = 1
    if theta_base > 120:
        sig = -1
    # 解释：
    # 上一段代码是一个名为get_kink_events的函数定义，该函数接受三个参数：theta，time_length和abs_B。这个函数似乎是在寻找某些事件。
    # 函数的第一步是设置几个阈值，这些阈值决定了事件的性质，如角度、时间等。然后，该函数计算出theta的前50%值，并将其设置为theta的基准值。然后，函数检查基准值是否小于50或大于120，并在这两种情况下将sig设置为1或-1。
    if sig == 0:
        events_list = []
    else:
        events_list = []
        delta_theta = sig * (theta - theta_base)
        delta_theta_norm_to0and1 = delta_theta
        delta_theta_norm_to0and1[delta_theta_norm_to0and1 <= theta_threshold] = 0
        delta_theta_norm_to0and1[delta_theta_norm_to0and1 > theta_threshold] = 1
        diff_delta_theta_norm_to0and1 = np.diff(delta_theta_norm_to0and1)
        beg_time_index = np.where(diff_delta_theta_norm_to0and1 == 1)[0]
        end_time_index = np.where(diff_delta_theta_norm_to0and1 == -1)[0]
        if end_time_index[0] < beg_time_index[0]:
            end_time_index = end_time_index[1:]
        if beg_time_index[-1] > end_time_index[-1]:
            beg_time_index = beg_time_index[:-1]
        try:
            exist_time = end_time_index - beg_time_index
        except EOFError:
            print('a')
        # 本段代码主要用于寻找磁场角度变化（theta）的kink事件。首先根据前面计算出的theta_base，将theta减去theta_base得到delta_theta，然后根据theta_threshold将delta_theta转换为二进制数组delta_theta_norm_to0and1。接下来计算delta_theta_norm_to0and1的一阶差分数组diff_delta_theta_norm_to0and1，并找到其值为1和-1的位置，分别存储在beg_time_index和end_time_index中。为了避免事件跨越数据段，需要对beg_time_index和end_time_index进行调整。最后计算exist_time表示每个事件的持续时间。如果sig为0，则表示没有kink事件，events_list为空。否则，events_list返回一个空列表，以便在后面添加事件。
        # 这一段缺失了，代码的解释如下：
        # 这段代码首先将两个数组 kink_end_time(non_kink_index) 和 kink_beg_time(non_kink_index) 清空，然后它开始一个循环，这个循环遍历了 kink_end_time 数组中的所有元素。在每次循环中，代码计算了一个 TimeLength 变量，该变量表示两个“kink”事件之间的时间长度的 1/3。接下来，代码计算了在 kink_end_time(j)-TimeLength 到 kink_end_time(j) 时间段内 theta 数组中的平均值 theta_average_in 和在 kink_end_time(j) 到 kink_end_time(j)+TimeLength 时间段内 theta 数组的平均值 theta_average_out。如果 theta_average_out 和 theta_average_in 之间的差异大于预设阈值 theta_threshold_of_kink_min，并且 abs_B_out 和 abs_B_in 之间的差异小于 abs_B_out 的 10%，则代码将此“kink”事件添加到 events_list 数组中。如果在此过程中发生错误，则代码将 events_list 数组设置为空。整个代码块嵌套在一个 try-catch 块中，以捕获任何可能的错误。
        kink_events = np.where(exist_time > exist_time_threshold)[0]
        kink_beg_time = beg_time_index(kink_events)
        kink_end_time = end_time_index(kink_events)
        temp_time = kink_beg_time[1:] - kink_end_time[:-1]
        index = np.where(temp_time < step_time_threshold)[0]
        kink_end_time = np.delete(kink_end_time, index)
        kink_beg_time = np.delete(kink_beg_time, index + 1)
        non_kink_index = []
        for j in range(len(kink_end_time)):
            time_length = np.floor((kink_end_time[j] - kink_beg_time[j]) / 3)
            if kink_end_time[j] + time_length > 86400:
                non_kink_index.append(j)
                continue
            theta_average_in = np.nanmean(theta[kink_end_time[j] - time_length:kink_end_time[j], 0])
            theta_average_out = np.nanmean(theta[kink_end_time[j]:kink_end_time[j] + time_length, 0])
            abs_B_in = np.nanmean(abs_B[kink_end_time[j] - time_length:kink_end_time[j], 0])
            abs_B_out = np.nanmean(abs_B[kink_end_time[j]:kink_end_time[j] + time_length, 0])
        if sig * (theta_average_in - theta_average_out) < theta_threshold_of_kink_min:
            non_kink_index.append(j)
        if sig * (theta_average_in - theta_average_out) > theta_threshold_of_kink_max:
            non_kink_index.append(j)
        kink_end_time = np.delete(kink_end_time, non_kink_index)
        kink_beg_time = np.delete(kink_beg_time, non_kink_index)
        events_list = np.zeros((len(kink_end_time), 2))
        num = 0
        for j in range(len(kink_end_time)):
            TimeLength = np.floor((kink_end_time[j] - kink_beg_time[j]) / 3)
            theta_average_in = np.nanmean(theta[kink_end_time[j] - TimeLength:kink_end_time[j], 0])
            theta_average_out = np.nanmean(theta[kink_end_time[j]:kink_end_time[j] + TimeLength, 0])
            if abs(theta_average_out - theta_average_in) > theta_threshold_of_kink_min:
                if abs(abs_B_out - abs_B_in) / abs_B_out < 0.1:
                    events_list[num, 0] = kink_beg_time[j]
                    events_list[num, 1] = kink_end_time[j]
                    num += 1
    return events_list

addpath = 'C:/Users/bella/Desktop/组会/cdf/'
data_dir = 'C:/Users/bella/Desktop/psp-data/'
for year_num in [2018 % 2020]:
    if year_num == 2018:
        month_num_arr = [11]
        day_num_arr = [[6]]  # 1:10
    elif year_num == 2019:
        month_num_arr = [4]
        day_num_arr = [list(range(1, 10))]
    elif year_num == 2020:
        month_num_arr = [1, 6, 9]
        day_num_arr = [list(range(20, 31)), list(range(2, 13)), list(range(22, 33))]
    elif year_num == 2021:
        month_num_arr = [1, 4, 8, 11]
        day_num_arr = [list(range(12, 23)), list(range(24, 35)), list(range(4, 15)), list(range(16, 27))]

    for month_numnum in range(len(month_num_arr)):
        month_num = month_num_arr[month_numnum]
        if year_num == 2020 and month_num == 6:
            data_dir = 'D:/psp_data/'
        for numnum in range(len(day_num_arr[month_numnum])):
            day_num = day_num_arr[month_numnum][numnum]
            if day_num > 30:
                day_num = day_num_arr[month_numnum][numnum] - 30
                month_num = month_num_arr[month_numnum] + 1
            for hour_num in range(0, 19, 6):
                year = str(year_num)
                month = f"{month_num:02d}"
                day = f"{day_num:02d}"
                hour = f"{hour_num:02d}"

                # Load data
                print(f"current_data_time: {year}-{month}-{day} {hour}")
                mag_filename = f"{data_dir}/psp_fld_l2_mag_rtn_{year}{month}{day}{hour}_v02.cdf"
                cdf_file = pycdf.CDF(mag_filename)
                b_rtn = cdf_file['psp_fld_l2_mag_RTN'][:]
                b_epoch = cdf_file['epoch_mag_RTN'][:]
                cdf_file.close()
                # b_rtn = pycdf.CDF('psp_fld_l2_mag_RTN', file_list=[mag_filename])
                # b_epoch = pycdf.CDF('epoch_mag_RTN', file_list=[mag_filename])
                b_rtn[np.abs(b_rtn) > 1e3] = np.nan

                # Interpolate data
                time_begin = datetime.strptime(year + '-' + month + '-' + day, '%Y-%m-%d')
                time_end = time_begin + timedelta(days=1)
                time_step = datetime.strptime('04-Nov-2018 00:00:01.00', '%d-%b-%Y %H:%M:%S.%f') - datetime.strptime(
                    '04-Nov-2018 00:00:00.00', '%d-%b-%Y %H:%M:%S.%f')
                STD_epoch = np.arange(time_begin.timestamp(), time_end.timestamp(), time_step.total_seconds())
                STD_epoch_seq = STD_epoch - STD_epoch[0]
                print(type(b_epoch))
                print(type(STD_epoch[0]))
                B_epoch_seq = pd.to_datetime(b_epoch) - pd.to_datetime(STD_epoch[0])
                B_epoch_seq= (B_epoch_seq/ np.timedelta64(1, 'D')).astype(float)
                d=len(b_rtn)
                b_r=b_rtn[:,0]
                b_t=b_rtn[:,1]
                b_n=b_rtn[:,2]
                #print(type(B_epoch_seq))
                #B=np.interp(STD_epoch_seq,B_epoch_seq,b_rtn)
                print(len(B_epoch_seq))
                print(len(b_r))
                print(np.asarray(B_epoch_seq).shape)
                print(np.asarray(b_r).shape)
                B_r = interp1d(B_epoch_seq,b_r, kind='linear',fill_value="extrapolate")(STD_epoch_seq)
                B_t = interp1d(B_epoch_seq, b_t, kind='linear',fill_value="extrapolate")(STD_epoch_seq)
                B_n = interp1d(B_epoch_seq, b_n, kind='linear',fill_value="extrapolate")(STD_epoch_seq)
                print(np.asarray(B_r).shape)
                B=np.array([B_r,B_t,B_n])
                #B= np.interp(np.array((B_epoch_seq/ timedelta(days=1), dtype='float64'),b_rtn/ timedelta(days=1), dtype='float64'))
                # b_epoch_seq = (b_epoch - b_epoch[0]) / 86400.0
                # b_interp = interp(b_epoch_seq, b_rtn, (np.array(std_epoch) - std_epoch[0]) * 86400.0)
                theta = get_theta(B)
                B_mag = get_norm(B)
                events_list=[]
                time_length = 9999# 60
                events_list = get_kink_events(theta, time_length, B_mag)
                # clear B_epoch_seq, Bp, time_end, STD_epoch, B_epoch, STD_epoch_seq, info
                if not events_list:
                    # 输出switchback的时间：
                    events_time_list = events_list
                else:
                    events_time_list = [time_begin + timedelta(seconds=event / 86400) for event in events_list]
                dir_switchback = 'C:/Users/bella/Desktop/pspSB/'
                filename_switchback = f"(prctile_50)(step_time_threshold_60)psp_kink_events_based_on_theta_BR_timelength_{str(time_length)}_{year}{month}{day}{hour}.mat"
                # save_dict = {'events_time_list': events_time_list}
                # scipy.io.savemat(dir_switchback + filename_switchback, save_dict)
                filepath_switchback = os.path.join(dir_switchback, filename_switchback)
                scipy.io.savemat(filepath_switchback, {'events_time_list': events_time_list})


