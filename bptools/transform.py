import warnings
from os.path import abspath, splitext, isfile
import numpy as np

from bptools.odin import ElectrodeConfig
from bptools.pairs import read_montage_json


class SeriesTransformation(object):
    def __init__(self):
        # matrix that recovers monopolar channnel readings from bipolar
        # recording
        self.bipolar_to_monopolar_matrix = None

        # monopolar to bipolar matrix
        self.monopolar_to_bipolar_matrix = None

        # instance of ElectrodeConfig
        self.elec_conf = None

        self.montage_data = None

        # montage data that describes which bp's to exclude
        self.excluded_montage_data = None

        # full_montage_data-excluded_montage_date - usually used to compute
        # classifiers
        self.net_montage_data = None

        self.montage_initialized = False

        self.bp_except_excluded_mask = None

    @classmethod
    def create(cls, electrode_config_file, montage_file=None, excluded_montage_file=None):
        """
        reads electrode config .csv file and stores ElectrodeConfig instance as member variable
        It also initializes transformation matrices (if possible) and configures bp_pairs-related variables
        that will be used in the ens_data_array -> monopolar or ens_data_array -> bipolar

        :param electrode_config_file: {str} path to electrode configuration file
        :return: None
        """

        st_obj = cls()
        electrode_config_file = abspath(electrode_config_file)
        electrode_config_file_core, ext = splitext(electrode_config_file)
        electrode_config_file_csv = electrode_config_file_core + '.csv'

        elec_conf = ElectrodeConfig(electrode_config_file_csv)
        # TODO check if we always have to include C/R in the electrode list
        st_obj.elec_conf = elec_conf

        # first we determine whether bipolar to monopolar transformation is possible

        # initializing  bipolar_2_monopolar_matrix - if possible
        st_obj.bipolar_to_monopolar_matrix = st_obj.monopolar_trans_matrix_via_inverse()

        # next we process montage
        st_obj.__initialize_montage(montage_file=montage_file, excluded_montage_file=excluded_montage_file)

        if st_obj.bipolar_to_monopolar_matrix is None:
            # we are in the full-bipolar mode and will extract implied bipolar pairs
            # setting up bipolar_pairs_signal implementation
            st_obj.bipolar_pairs_signal = st_obj._bipolar_pairs_signal_full_bp_mode_impl
        else:
            if st_obj.montage_initialized:
                st_obj.bipolar_pairs_signal = st_obj._bipolar_pairs_signal_mixed_mode_impl

        return st_obj


    @property
    def bipolar_pairs_recarray(self):
        """
        Returns montage recarray
        :return: {ndarray} montage recarray with the following columns:
        (contact_name, ch0_label, ch1_label, ch1_idx, ch1_idx)
        """
        return self.montage_data

    @property
    def net_bipolar_pairs_recarray(self):
        """
        Returns montage recarray but does not include excluded pairs
        :return: {ndarray} montage recarray with the following columns:
        (contact_name, ch0_label, ch1_label, ch1_idx, ch1_idx)
        """

        return self.net_montage_data

    @property
    def monopolar_recarray(self):
        """
        Returns contacts recarray (as declared int he electrode configuration)
        :return: {ndarray} contacts recarray witht eh following columns
        (jack_box_num,contact_name, description)
        """

        return self.elec_conf.contacts_as_recarray()

    @property
    def sense_channel_recarray(self):
        """
        Returns contacts recarray (as declared int he electrode configuration)
        :return: {ndarray} contacts recarray witht eh following columns
        (jack_box_num,contact_name, description)
        """
        return self.monopolar_recarray


    @property
    def num_sense_channels(self):
        """
        Returns number of sense channels as stored int he elec_conf
        :return: {int}
        """
        return len(self.elec_conf.sense_channels)

    @property
    def num_all_bp(self):
        """
        Returns number of ALL bipolar_pairs (if montage is provided or if full bp config is inplace)
        :return: {int}
        """
        if self.montage_initialized:
            if self.montage_data.ch0_idx is not None:
                return len(self.montage_data.ch0_idx)
            else:
                raise RuntimeError("Improper initialization of the montage ")

        raise RuntimeError(
            "Montage missing and could not determine implied_bipolar_pairs - "
            "likely mixed_mode with missing montage")

    @property
    def net_num_bp(self):
        """ returns number of bipolar pairs in the net montage data. Typically used in classifier computations
        Note this is not necessarily the number of total sensing bipolar pairs, because some of the bps
        could have been excluded in the net_montage_data
        :return: {int} number of bps
        """

        if self.montage_initialized:
            if self.net_montage_data.ch0_idx is not None:
                return len(self.net_montage_data.ch0_idx)
            else:
                raise RuntimeError("Improper initialization of the montage ")

        raise RuntimeError(
            "Montage missing and could not determine implied_bipolar_pairs - likely mixed_mode with missing montage")

    def __initialize_montage(self, montage_file=None, excluded_montage_file=None):
        """
        Parses montage data . Initializes three SeriesTransformation members:
        self.full_montage_data
        self.excluded_montage_data
        self.net_montage_data
        This function relies on the knowledge whether we are in the mixed mode or fully bp mode.
        Therefore it can only be called after we tried to extract bipolar to monopolar matrix

        :param montage_file: {str} - montage file - paris.json or int he fully bipolar mode we can leave it empty
        :param excluded_montage_file: {str} - montage file with excluded pairs
        :return: None
        """

        if self.monopolar_possible():
            if not montage_file:
                return
            self.montage_data = read_montage_json(montage_file)
        else:
            self.montage_data = self.__get_implied_montage()

        if excluded_montage_file is not None and isfile(excluded_montage_file):
            self.excluded_montage_data = read_montage_json(excluded_montage_file)

            all_excluded_present = np.in1d(self.excluded_montage_data.contact_name, self.montage_data.contact_name)
            if not np.all(all_excluded_present):
                warnings.warn(
                    'some of the excluded pairs: {} '
                    'are not present in the montage'.format(str(self.excluded_montage_data.contact_name)),
                    RuntimeWarning)

            self.bp_except_excluded_mask = ~ np.in1d(self.montage_data.contact_name, self.excluded_montage_data.contact_name)

            self.net_montage_data = self.montage_data[self.bp_except_excluded_mask]
        else:
            self.net_montage_data = self.montage_data

        # TODO careful here
        self.montage_initialized = True

    def bipolar_possible(self):
        """
        Determines whether SeriesTransformation can produce bipolar pairs time
        series from  ens_time_series

        :rtype: bool
        """
        try:
            a = self.num_all_bp
        except:
            return False
        return True

    def monopolar_possible(self):
        """
        Determines whether we can recover monopolar recordings or not
        :return: {bool} "false" means that we can only get bipolar time series
        "false" means we can recover bipolar recordings
        """
        return self.bipolar_to_monopolar_matrix is not None

    def _bipolar_pairs_signal_mixed_mode_impl(self, ens_signal_array, exclude_bipolar_pairs=False):
        """bipolar_pairs_signal implementation when monopolar_recording recovery
        is possible AND montage has been initialized

        :param ens_signal_array: 2D array (or nm.matrix) with the following dimensions (num_channels, sample_len)
        :param exclude_bipolar_pairs: {bool} specifies whether bipolar time series should be based on full set of
        bipolar pairs (as speciofied in the self. montage_data) or whether
        we should exclude bipolar pairs (specified in self.excluded_montage_data)
        :return: {ndarray} bipolar time series
        """

        monopolar_signal_array = self.transform_signal(ens_signal_array=ens_signal_array)
        if exclude_bipolar_pairs:
            return monopolar_signal_array[self.net_montage_data.ch0_idx] - monopolar_signal_array[
                self.net_montage_data.ch1_idx]

        return monopolar_signal_array[self.montage_data.ch0_idx] - monopolar_signal_array[self.montage_data.ch1_idx]

    def _bipolar_pairs_signal_full_bp_mode_impl(self, ens_signal_array, exclude_bipolar_pairs=False):
        """
        bipolar_pairs_signal implementation in the full bipolar mode
        :param ens_signal_array: 2D array (or nm.matrix) with the following dimensions (num_channels, sample_len)
        :param exclude_bipolar_pairs: {bool} specifies whether bipolar time series should be based on full set of
        bipolar pairs (as speciofied in the self. montage_data) or whether
        we should exclude bipolar pairs (specified in self.excluded_montage_data)
        :return: {ndarray} bipolar time series
        """

        # TODO handle the case of excluded pairs
        if exclude_bipolar_pairs:
            return ens_signal_array[self.bp_except_excluded_mask]

        return ens_signal_array

    def bipolar_pairs_signal(self, ens_signal_array, exclude_bipolar_pairs=False):
        """
        Tries to reconstruct monopolar recordings from the ens_recordings and then use bipolar_pairs.json to
        construct bipolar time series. If the bipolar-to-monopolar is impossible then we are
        in the fully bipolar-sensing mode and then we simply return ens_signal_array

        :param ens_signal_array: 2D array (or nm.matrix) with the following
            dimensions (num_channels, sample_len)
        :param exclude_bipolar_pairs: {bool} specifies whether bipolar time
            series should be based on full set of bipolar pairs (as speciofied
            in the self. montage_data) or whether
            we should exclude bipolar pairs (specified in
            self.excluded_montage_data)
        :return: {ndarray} bipolar time series

        """

        if self.monopolar_possible() and not self.montage_initialized:
            raise RuntimeError("Mixed-model referencing error: "
                               "to use bipolar_pairs_signal one needs to provide montage to SeriesTransformation")

        raise RuntimeError("bipolar_pairs_signal was not setup correctly ")

    def transform_signal(self, ens_signal_array):
        """
        Applies bipolar-to-monopolar transformation to recover monopolar readings (if possible)

        Here is an example:
        you get EEG signal - make sure that each row is a time series representing single channel recording (
        i.e. your eeg array (EEG_ARRAY) should look like


            time---------------->
        0  | 12, 23, 45,56 67, 78, 78 78
        1  | 34 45 56 67 78 23 45 56 56
        2  | 23 45 56 23 45 667 67 34 23
        ...
        100 |
        ^
        |
        channels

        The transformation then is
        EEG_ARRAYTRANSFORMED = transformation_matrix * EEG_ARRAY

        If such transformation is not possible it means we are in the fully bipolar mode and then we return signal_array
        because there is not transformation to be made

        :param ens_signal_array: 2D array (or nm.matrix) with the following dimensions (num_channels, sample_len)
        :return:numpy array shape=(num_channels, sample_len) of monopolar readings
        or signal_array if bipolar_2_monopolar transformation is impossible
        """

        if self.bipolar_to_monopolar_matrix is None:
            return ens_signal_array

        # doing the transformation and returning numpy array back
        converted_array = np.array(self.bipolar_to_monopolar_matrix * np.asmatrix(ens_signal_array))
        return converted_array

    def monopolar_signal(self, ens_signal_array):
        """
        Uses bipolar_2_monopolar_transformation to extract monopolar_recordings if monopolar recordings are possible
        Otherwise raises exception

        :param ens_signal_array: 2D array (or nm.matrix) with the following dimensions (num_sense_channels, sample_len)
        :return: monopolar signal numpy array shape=(num_monopolar_channels, sample_len)
        """
        if not self.monopolar_possible():
            raise RuntimeError("Extracting monopolar signal in the fully bp mode is impossible")

        return self.bipolar_2_monopolar_transformation(ens_signal_array=ens_signal_array)

    def bipolar_2_monopolar_transformation(self, ens_signal_array):
        """
        Applies bipolar to monopolar transformation to recover monopolar readings

        Here is an example:
        you get EEG signal - make sure that each row is a time series representing single channel recording (
        i.e. your eeg array (EEG_ARRAY) should look like


            time---------------->
        0  | 12, 23, 45,56 67, 78, 78 78
        1  | 34 45 56 67 78 23 45 56 56
        2  | 23 45 56 23 45 667 67 34 23
        ...
        100 |
        ^
        |
        channels

        The transformation then is
        EEG_ARRAYTRANSFORMED = transformation_matrix * EEG_ARRAY

        :param ens_signal_array: 2D array (or nm.matrix) with the following dimensions (num_channels, sample_len)
        :return:numpy array shape=(num_channels, sample_len) of monopolar readings
        """

        if self.bipolar_to_monopolar_matrix is None:
            return ens_signal_array

        # doing the transformation and returning numpy array back
        converted_array = np.array(self.bipolar_to_monopolar_matrix * np.asmatrix(ens_signal_array))
        return converted_array

    def __get_implied_montage(self):
        """return a recarray of implied bipolar pairs. Implied bipolar pairs are the pairs that are encoded in the
        electrode config sense configuration. We assume that bipolar pairs are sorted by first channel label. I.e.
        self.get_monopolar_to_bipolar_matrix() is such that impliedbipolar pairs are sorted
        :return: {nd.recarray} dtype is np.dtype(
            [('ch0_idx', '<i8'), ('ch1_idx', '<i8'), ('ch0_label', '|S256'), ('ch1_label', '|S256'),
             ('contact_name', '|S256')])

        """
        tr_mat = self.get_monopolar_to_bipolar_matrix()

        # storing matrix before removing zero columns
        # the enstries from this matrix are meaningful if we process elec_cont.contacts
        self.monopolar_to_bipolar_matrix = np.matrix(tr_mat)

        # implied_bp_dtype = np.dtype([('e0', '<i8'), ('e1', '<i8'), ('bp_name', '|S256')])
        implied_bp_dtype = np.dtype(
            [('ch0_idx', '<i8'), ('ch1_idx', '<i8'), ('ch0_label', '|S256'), ('ch1_label', '|S256'),
             ('contact_name', '|S256')])

        # self.configure_bipolar_2_monopolar_transformation(electrode_config_file)
        m2b = self.monopolar_to_bipolar_matrix

        bp_idx_list = []

        for i in range(m2b.shape[0]):
            try:
                e_sense_idx = np.where(m2b[i, :] == 1)[1][0]
                e_ref_idx = np.where(m2b[i, :] == -1)[1][0]
                bp_idx_list.append((e_sense_idx, e_ref_idx))
            except IndexError:
                pass

        contacts = self.elec_conf.contacts
        contact_labels = [contact.label for contact in contacts]

        contacts_recarray = self.elec_conf.contacts_as_recarray()

        e_array = np.recarray((len(bp_idx_list),), dtype=implied_bp_dtype)
        for i, (e_sense_idx, e_ref_idx) in enumerate(bp_idx_list):
            # NOTE: in the fully bp mode ch0_idx and ch1_idx are meaningless
            e_ref_name_idx = np.where(contacts_recarray.jack_box_num == e_ref_idx+1)[0][0]
            e_sense_name_idx = np.where(contacts_recarray.jack_box_num == e_sense_idx+1)[0][0]

            e_array[i]['ch1_idx'] = e_ref_name_idx
            e_array[i]['ch0_idx'] = e_sense_name_idx

            e_ref_name = contact_labels[e_ref_name_idx]
            e_sense_name = contact_labels[e_sense_name_idx]

            e_array[i]['ch1_label'] = str(contacts_recarray[e_ref_name_idx]['jack_box_num']).zfill(3)
            e_array[i]['ch0_label'] = str(contacts_recarray[e_sense_name_idx]['jack_box_num']).zfill(3)
            e_array[i]['contact_name'] = '{}-{}'.format(e_sense_name, e_ref_name)

        return e_array

    def configure_bipolar_2_monopolar_transformation(self, electrode_config_file):
        """reads bipolar-to-monopolar transformation matrix from the disk. In the future we may
        generate this matrix on the fly if the proposed referencing scheme works as desired

        :param electrode_config_file: {str} path to electrode configuration file
        :param subject: {str} subject code (e.g. R1232N)
        :return: None

        """

        electrode_config_file = abspath(electrode_config_file)
        electrode_config_file_core, ext = splitext(electrode_config_file)
        electrode_config_file_csv = electrode_config_file_core + '.csv'

        # TODO check if we always have to include C/R in the electrode list
        elec_conf = ElectrodeConfig(electrode_config_file_csv)
        self.elec_conf = elec_conf
        self.bipolar_to_monopolar_matrix = self.monopolar_trans_matrix_via_inverse(elec_conf)

    def get_monopolar_to_bipolar_matrix(self):
        """Constructs monopolar to bipolar transformation matrix
        The algorithm is as follows:
        1. We declare 256x256 zero matrix (because we can expect at most 256 sense channels in the ENS
        2. We iterate over sense channels (sorted by jackbox number) and put 1 in the [jack_box_num, jack_box_num] position
        and -1 in the [jack_box, ref_jack_box_num]
        :param elec_conf: {instance of ElectrodeConfig}
        :return: {ndarray} monopolar to bipolar matrix as ndarray

        """
        elec_conf = self.elec_conf
        if elec_conf is None:
            raise RuntimeError("elec_conf not specified. Make sure you create SeriesTransformatin using"
                               " Seriestransformation.create(elec_conf_file_path) syntax ")

        tr_mat = np.zeros((256, 256), dtype=np.int)
        for i, sense_channel in enumerate(elec_conf.sense_channels):
            port_num = sense_channel.contact
            tr_mat[port_num - 1, port_num - 1] = 1

            ref_num = int(sense_channel.ref)
            if ref_num != 0:
                tr_mat[port_num - 1, ref_num - 1] = -1

        # tr_mat = np.matrix(tr_mat)

        return tr_mat

    def monopolar_trans_matrix_via_inverse(self, elec_conf=None):
        """
        Function that computes transformation matrix that takes mixed mode (a.k. Medtronic bipolar) recording and
        transforms it into monopolar recordings.
        IMPORTANT: the algoritm implemented in this function works only for the mixed-mode referencing scheme
        proposed by Medtronic - i.e. banks of 16 electrodes where one electrode is connected to C/R  and
        other electrode in the bank reference it

        Here is what we are doing:
        Example

        E1 - connected to CR
        E2, E2 ,E3 are referenced to E1

        and in the experiment we measure E1, E2E1, E3E1, E4E1

        For this we get the following system of eqns
        E1 = E1
        E2 - E1 = E2E1
        E3 - E1 = E3E1
        E4 - E1 = E4E1

        or in matrix form

        | 1  0  0  0 |  |E1|   | E1   |
        | -1 1  0  0 |  |E2|   | E2E1 |
        | -1 0  1  0 |* |E3| = | E3E1 |
        | -1 0  0  1 |  |E4|   | E3E1 |

        or

        A*E_monopolar = E_bipolar

        Therefore to find monopolar recordings ew invert matrix A

        :return: {numpy matrix} transformation matrix - mixed-mode -> monopolar. This is the inverse of A
        """
        if elec_conf is None:
            if self.elec_conf is not None:
                elec_conf = self.elec_conf
            else:
                raise RuntimeError("elec_conf not specified. Make sure you create SeriesTransformatin using"
                                   " Seriestransformation.create(elec_conf_file_path) syntax ")

        tr_mat = self.get_monopolar_to_bipolar_matrix()

        # storing matrix before removing zero columns
        # the enstries from this matrix are meaningful if we process elec_cont.contacts
        self.monopolar_to_bipolar_matrix = np.matrix(tr_mat)

        # non_zero_mask = np.any(tr_mat != 0, axis=1)
        # self.monopolar_to_bipolar_matrix = self.monopolar_to_bipolar_matrix[non_zero_mask, :]

        # removing zero rows and columns
        non_zero_mask_row = np.any(tr_mat != 0, axis=1)
        non_zero_mask_column = np.any(tr_mat != 0, axis=0)
        tr_mat = tr_mat[non_zero_mask_row, :]
        tr_mat = tr_mat[:, non_zero_mask_column]

        tr_mat = np.matrix(tr_mat)

        # self.monopolar_to_bipolar_matrix = tr_mat

        try:
            tr_mat_inv = np.linalg.inv(tr_mat)
        except np.linalg.linalg.LinAlgError:
            return None

        return tr_mat_inv
