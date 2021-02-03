from Common import HoonUtils as utils


def create_multi_svr_ini(_this_basename_, ini_fname, proc_offset, port_inc=10):
    ini = utils.get_ini_parameters(ini_fname)
    if proc_offset >= 0:
        logger_name = ini['LOGGER']['name'] + '_{}'.format(proc_offset+1)

        ini['LOGGER']['name'] = logger_name
        ini['LOGGER']['prefix'] = logger_name + '.'
        ini['LOGGER']['folder'] = 'Log/{}/'.format(proc_offset+1)

        ini['SERVER_MODE']['name'] = logger_name
        ini['SERVER_MODE']['port'] = str(int(ini['SERVER_MODE']['port']) + proc_offset * port_inc)
        ini['SERVER_MODE']['acronym'] = ini['SERVER_MODE']['acronym'] + '{}'.format(proc_offset+1)

    return ini
