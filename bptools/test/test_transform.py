import os.path as osp
import unittest

import h5py
import numpy as np
from numpy.testing import assert_array_almost_equal
from pkg_resources import resource_filename
import pytest

from bptools.pairs import read_montage_json
from bptools.transform import SeriesTransformation


# FIXME: remove hard-coded paths
class TestSeriesTransformation(unittest.TestCase):
    def setUp(self):
        self.data_dir = osp.join((osp.dirname(__file__)), 'data')

    @pytest.mark.skip
    def test_get_monopolar_to_bipolar_matrix(self):
        input_output_dict = {
            'R1111M_FromJsonBpolAuto.csv': 'R1111M_FromJsonBpolAuto_matrix.h5',
            'bipolar_only.csv': None
        }

        for elec_csv_path, ans_path in input_output_dict.items():
            expect_failure = False
            elec_csv_abspath = osp.join(self.data_dir, elec_csv_path)

            if not ans_path:
                expect_failure = True
            else:
                ans_path_abspath = osp.join(self.data_dir, ans_path)

                with h5py.File(ans_path_abspath, 'r') as ans_file:
                    stored_bipol_2_mono_tr_mat = ans_file['bipolar_to_monopolar_matrix'].value

            st = SeriesTransformation.create(elec_csv_abspath)
            computed_bipol_2_mono_tr_mat = st.bipolar_to_monopolar_matrix

            if not expect_failure:
                assert_array_almost_equal(computed_bipol_2_mono_tr_mat, stored_bipol_2_mono_tr_mat)
            else:
                assert computed_bipol_2_mono_tr_mat is None, ' Expecting computed_bipol_2_mono_tr_mat to be None'

    @pytest.mark.skip
    def test_ens_series_transform(self):
        local_data_dir = osp.join(self.data_dir, 'R1111Q_mixed_mode')

        with h5py.File(osp.join(local_data_dir, 'eeg_timeseries.h5'), 'r') as in_h5:
            timeseries = in_h5['timeseries'].value
            b2m_mat = in_h5['bipolar_to_monopolar_matrix'].value

        montage_file = osp.join(local_data_dir, 'pairs.json')
        excluded_montage_file = osp.join(local_data_dir, 'excluded_pairs.json')
        elec_csv_abspath = osp.join(local_data_dir, 'elec_conf_mixed_mode.csv')

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
        local_data_dir = osp.join(self.data_dir, 'R1111Q_mixed_mode')

        montage_file = osp.join(local_data_dir, 'pairs.json')
        excluded_montage_file = osp.join(local_data_dir, 'excluded_pairs.json')
        elec_csv_abspath_mm = osp.join(local_data_dir, 'elec_conf_mixed_mode.csv')

        st = SeriesTransformation.create(elec_csv_abspath_mm, montage_file=montage_file,
                                         excluded_montage_file=excluded_montage_file)

        assert st.net_num_bp == 135, " TEST of {} failed".format(elec_csv_abspath_mm)

        # testing bipolar only
        elec_csv_abspath_bp = osp.join(self.data_dir, 'bipolar_only.csv')

        st = SeriesTransformation.create(elec_csv_abspath_bp)

        assert st.net_num_bp == 102, " TEST of {} failed".format(elec_csv_abspath_bp)

        # testing mixed mode without montages
        st = SeriesTransformation.create(elec_csv_abspath_mm)
        with self.assertRaises(RuntimeError) as ctx:
            assert st.net_num_bp == 135, " TEST of {} failed".format(elec_csv_abspath_mm)

    def test_num_all_bp(self):
        local_data_dir = osp.join(self.data_dir, 'R1111Q_mixed_mode')

        montage_file = osp.join(local_data_dir, 'pairs.json')
        excluded_montage_file = osp.join(local_data_dir, 'excluded_pairs.json')
        elec_csv_abspath_mm = osp.join(local_data_dir, 'elec_conf_mixed_mode.csv')

        st = SeriesTransformation.create(elec_csv_abspath_mm, montage_file=montage_file,
                                         excluded_montage_file=excluded_montage_file)

        assert st.num_all_bp == 141, " TEST of {} failed".format(elec_csv_abspath_mm)

    def test_bipolar_monopolar_possible(self):
        local_data_dir = osp.join(self.data_dir, 'R1308T_full_bp')
        elec_csv_abspath = osp.join(local_data_dir, 'R1308T_FULLBPDEMO.csv')

        st = SeriesTransformation.create(elec_csv_abspath)

        assert not st.monopolar_possible(), 'Expected that monopolar model will be impossible'
        assert st.bipolar_possible(), 'Expected that bipolar model will be possible'

        # monopolar but without montage
        elec_csv_abspath = osp.join(local_data_dir, 'R1308T_R1308T08JUNE2017NOSTIM.csv')

        st = SeriesTransformation.create(elec_csv_abspath)
        assert st.monopolar_possible(), 'Expected that monopolar model will be impossible'
        assert not st.bipolar_possible(), 'Expected that bipolar model will be possible'
