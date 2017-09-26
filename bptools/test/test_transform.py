from os.path import *
import unittest
import pytest

import numpy as np
from numpy.testing import assert_array_almost_equal
import h5py

from bptools.pairs import read_montage_json
from bptools.transform import SeriesTransformation


# FIXME: remove hard-coded paths
class TestSeriesTransformation(unittest.TestCase):
    def setUp(self):
        self.data_dir = join((dirname(__file__)), 'series_transformation_data')

    @pytest.mark.skip
    def test_extract_hdf_array(self):
        """
        temporary helper fcn
        :return:
        """
        hdf_file = r'd:\SYS3_testdata_bipolar\R1111Q\FR5\20170726_160338\eeg_timeseries.h5'
        with h5py.File(hdf_file, 'r') as eeg_hfile:
            matrix = eeg_hfile['bipolar_to_monopolar_matrix'].value
            timeseries = eeg_hfile['timeseries'].value

            with h5py.File(join(self.data_dir, 'R1111Q_short_session.h5'), 'w') as out_h5:
                out_h5['bipolar_to_monopolar_matrix'] = matrix
                out_h5['timeseries'] = timeseries[:100, :]

    @pytest.mark.skip
    def test_get_monopolar_to_bipolar_matrix(self):

        input_output_dict = {
            'R1111M_FromJsonBpolAuto.csv': 'R1111M_FromJsonBpolAuto_matrix.h5',
            'bipolar_only.csv': None
        }

        for elec_csv_path, ans_path in input_output_dict.items():
            expect_failure = False
            elec_csv_abspath = join(self.data_dir, elec_csv_path)

            if not ans_path:
                expect_failure = True
            else:
                ans_path_abspath = join(self.data_dir, ans_path)

                with h5py.File(ans_path_abspath, 'r') as ans_file:
                    stored_bipol_2_mono_tr_mat = ans_file['bipolar_to_monopolar_matrix'].value

            st = SeriesTransformation.create(elec_csv_abspath)
            computed_bipol_2_mono_tr_mat = st.bipolar_to_monopolar_matrix
            # computed_bipol_2_mono_tr_mat = st.monopolar_trans_matrix_via_inverse()

            if not expect_failure:
                assert_array_almost_equal(computed_bipol_2_mono_tr_mat, stored_bipol_2_mono_tr_mat)
            else:
                assert computed_bipol_2_mono_tr_mat is None, ' Expecting computed_bipol_2_mono_tr_mat to be None'

    @pytest.mark.skip
    def test_ens_series_transform(self):

        local_data_dir = join(self.data_dir, 'R1111Q_mixed_mode')

        with h5py.File(join(local_data_dir, 'eeg_timeseries.h5'), 'r') as in_h5:
            timeseries = in_h5['timeseries'].value
            b2m_mat = in_h5['bipolar_to_monopolar_matrix'].value

        montage_file = join(local_data_dir, 'pairs.json')
        excluded_montage_file = join(local_data_dir, 'excluded_pairs.json')
        elec_csv_abspath = join(local_data_dir, 'elec_conf_mixed_mode.csv')

        montage_data = read_montage_json(montage_file)

        if excluded_montage_file is not None:
            excluded_montage_data = read_montage_json(excluded_montage_file)

            bp_except_excluded_mask = ~ np.in1d(montage_data.contact_name, excluded_montage_data.contact_name)
            montage_data = montage_data[bp_except_excluded_mask]

        ch0_idx = montage_data.ch0_idx
        ch1_idx = montage_data.ch1_idx

        st = SeriesTransformation.create(elec_csv_abspath, montage_file=montage_file,
                                         excluded_montage_file=excluded_montage_file)

        bp_eegs_from_st = st.bipolar_pairs_signal(timeseries, exclude_bipolar_pairs=True)

        monopolar_eegs = b2m_mat * np.matrix(timeseries)
        bp_eegs_manual = monopolar_eegs[ch0_idx] - monopolar_eegs[ch1_idx]

        assert_array_almost_equal(bp_eegs_from_st, bp_eegs_manual)

        # test bipolar_pairs_signal without providing montage
        with self.assertRaises(RuntimeError) as ctx:
            st = SeriesTransformation.create(elec_csv_abspath)
            bp_eegs_from_st = st.bipolar_pairs_signal(timeseries)

    @pytest.mark.skip
    def test_num_bp(self):

        # testing mixed mode
        local_data_dir = join(self.data_dir, 'R1111Q_mixed_mode')

        montage_file = join(local_data_dir, 'pairs.json')
        excluded_montage_file = join(local_data_dir, 'excluded_pairs.json')
        elec_csv_abspath_mm = join(local_data_dir, 'elec_conf_mixed_mode.csv')

        st = SeriesTransformation.create(elec_csv_abspath_mm, montage_file=montage_file,
                                         excluded_montage_file=excluded_montage_file)

        assert st.net_num_bp == 135, " TEST of {} failed".format(elec_csv_abspath_mm)

        # testing bipolar only
        elec_csv_abspath_bp = join(self.data_dir, 'bipolar_only.csv')

        st = SeriesTransformation.create(elec_csv_abspath_bp)

        assert st.net_num_bp == 102, " TEST of {} failed".format(elec_csv_abspath_bp)

        # testing mixed mode without montages
        st = SeriesTransformation.create(elec_csv_abspath_mm)
        with self.assertRaises(RuntimeError) as ctx:
            assert st.net_num_bp == 135, " TEST of {} failed".format(elec_csv_abspath_mm)

    @pytest.mark.skip
    def test_num_all_bp(self):

        local_data_dir = join(self.data_dir, 'R1111Q_mixed_mode')

        montage_file = join(local_data_dir, 'pairs.json')
        excluded_montage_file = join(local_data_dir, 'excluded_pairs.json')
        elec_csv_abspath_mm = join(local_data_dir, 'elec_conf_mixed_mode.csv')

        st = SeriesTransformation.create(elec_csv_abspath_mm, montage_file=montage_file,
                                         excluded_montage_file=excluded_montage_file)

        assert st.num_all_bp == 141, " TEST of {} failed".format(elec_csv_abspath_mm)

    @pytest.mark.skip
    def test_bipolar_monopolar_possible(self):
        local_data_dir = join(self.data_dir, 'R1308T_full_bp')
        elec_csv_abspath = join(local_data_dir, 'R1308T_FULLBPDEMO.csv')

        st = SeriesTransformation.create(elec_csv_abspath)

        assert st.monopolar_possible() == False, 'Expected that monopolar model will be impossible'
        assert st.bipolar_possible() == True, 'Expected that bipolar model will be possible'

        # monopolar but without montage
        elec_csv_abspath = join(local_data_dir, 'R1308T_R1308T08JUNE2017NOSTIM.csv')

        st = SeriesTransformation.create(elec_csv_abspath)
        assert st.monopolar_possible() == True, 'Expected that monopolar model will be impossible'
        assert st.bipolar_possible() == False, 'Expected that bipolar model will be possible'

    @pytest.mark.skip
    def test_monopolar_2_bipolar(self):
        local_data_dir = join(self.data_dir, 'R1308T_full_bp')
        elec_csv_abspath = join(local_data_dir, 'R1308T_FULLBPDEMO.csv')

        st = SeriesTransformation.create(elec_csv_abspath)

        # # get monopolar_hdf5
        # eeg_h5 = join(local_data_dir, 'eeg_timeseries.h5')
        # with h5py.File(eeg_h5, 'r') as eeg_hfile:
        #     timeseries = eeg_hfile['timeseries'].value

        data_root = r'd:\SYS3_testdata\R1308T_full_bp\FR1'
        sessions = [0, 1, 2, 3, 4]

        for session in sessions:
            timeseries_filename = join(data_root, 'session_{:d}'.format(session), 'eeg_timeseries.h5')
            timeseries_filename_out = join(data_root, 'session_{:d}'.format(session), 'eeg_timeseries_bp_new.h5')
            with h5py.File(timeseries_filename, 'r') as eeg_hfile:
                timeseries = eeg_hfile['timeseries'].value
                bps = timeseries[:, st.montage_data.ch0_idx] - timeseries[:, st.montage_data.ch1_idx]


                with h5py.File(timeseries_filename_out, 'w') as out_h5:
                    out_h5['timeseries'] = bps
                    out_h5.attrs['recording_mode'] = 'bipolar'

                    bipolar_pairs_recarray = st.bipolar_pairs_recarray
                    if st.monopolar_possible():
                        # out_h5.create_array('/', 'monopolar_possible', np.array([1], dtype=np.int))
                        out_h5['monopolar_possible'] = np.array([1], dtype=np.int)
                    else:
                        # out_h5.create_array('/', 'monopolar_possible', np.array([0], dtype=np.int))
                        out_h5['monopolar_possible'] = np.array([0], dtype=np.int)

                    if bipolar_pairs_recarray is not None:
                        out_h5.create_group('bipolar_info')
                        out_h5['bipolar_info']['contact_name'] = bipolar_pairs_recarray.contact_name.astype('S256')
                        out_h5['bipolar_info']['ch0_label'] = bipolar_pairs_recarray.ch0_label.astype('S256')
                        out_h5['bipolar_info']['ch1_label'] = bipolar_pairs_recarray.ch1_label.astype('S256')

                    sense_channel_recarray = st.sense_channel_recarray

                    if sense_channel_recarray is not None:
                        out_h5.create_group('sense_channel_info')
                        out_h5['sense_channel_info']['contact_name'] = sense_channel_recarray.contact_name.astype('S256')
                        out_h5['sense_channel_info']['port_name'] = sense_channel_recarray.port_electrode.astype('i8')

                        out_h5['ports'] = sense_channel_recarray.port_electrode.astype('i8')
                        out_h5['names'] = sense_channel_recarray.contact_name.astype('S256')
