


class DataUtils:

    def get_obj_name_and_type_from_obj_info(obj_info, full_type=False):
        [OBJID_I, NAME_I, TYPE_I, SAVE_DATE_I, VERSION_I, SAVED_BY_I, WSID_I, WORKSPACE_I, CHSUM_I, SIZE_I, META_I] = list(range(11))  # object_info tuple
        obj_name = obj_info[NAME_I]
        obj_type = obj_info[TYPE_I].split('-')[0]
        if not full_type:
            obj_type = obj_type.split('.')[1]
        return (obj_name, obj_type)

