"""
This file sets up the resource class for getting and updating files &
information associated with a given resource in Jupyterhub & Hydroshare.

Author: 2019-20 CUAHSI Olin SCOPE Team
Email: vickymmcd@gmail.com
"""
#!/usr/bin/python
# -*- coding: utf-8 -*-

from hydroshare_jupyter_sync.config_reader_writer import get_config_values
from hydroshare_jupyter_sync.local_folder import LocalFolder
from hydroshare_jupyter_sync.hydroshare_folder import RemoteFolder
from notebook.services.contents.filemanager import FileContentsManager
import logging
import os
from os import path
from dateutil.parser import parse
import datetime
# note from Kyle for Charlie: you mean change to import pathlib as pl?
from pathlib import * # TODO: Charlie, change to pl for readability
import shutil

# TODO: we should probably rename all "JH" to "local" or just "jupyter" or something like that, since this is supposed
# to be platform-independent
HS_PREFIX = 'hs'
LOCAL_PREFIX = 'local'


class Resource:
    """ Class that defines a Hydroshare resource & it's associated files that
    are local to Jupyterhub.
    """

    def __init__(self, res_id, resource_handler):
        """Authenticates Hydroshare & sets up class variables.
        """
        self.res_id = res_id
        self.resource_handler = resource_handler
        self.output_folder = self.resource_handler.output_folder
        self.hs = self.resource_handler.hs

        # TODO: rename REmoteFolder class
        self.remote_folder = RemoteFolder(self.hs, self.res_id)
        self.local_folder = LocalFolder()

        self.path_prefix = Path(self.output_folder) / self.res_id / self.res_id / 'data' / 'contents'
        self.hs_files = self.get_files_upon_init_HS()
        self.JH_files = self.get_files_upon_init_JH()


    def create_file_JH(self, filename):
        """Creates a new file with the given name in JH
        """
        # TODO: TEST THIS! & add more error checking to this function, does it exist?
        if filename is not None:
            full_path = self.path_prefix / filename
            path_rel_cwd = Path(full_path).relative_to(Path.cwd())
            if filename.lower().endswith('.ipynb'):
                FileContentsManager().new(path=str(path_rel_cwd))
            else:
                full_path.touch()

    def create_local_folder(self, folder_name):
        """Creates a new file with the given name in JH
        """
        folder_path = self.path_prefix / folder_name
        if folder_path.exists():
            if folder_path.is_dir():
                return  # Directory exists, so just ignore the request
            else:
                raise IOError(f'Directory {str(folder_path)} exists')

        folder_path.mkdir()

    def save_resource_locally(self, unzip=True):
        """Saves the HS resource locally, if it does not already exist.
        """
        # Get resource from HS if it doesn't already exist locally
        if not os.path.exists('{}/{}'.format(self.output_folder, self.res_id)):

            logging.info("Downloading resource from HydroShare...")
            self.hs.getResource(self.res_id, destination=self.output_folder, unzip=unzip)

    def get_files_JH(self):
        # TODO (kyle): cache nonsense
        return self.JH_files

    def get_files_upon_init_JH(self):
        """Gets metadata for all the files currently stored in the JH instance
        of this resource.
        """

        self.save_resource_locally()
        resource_files_root_path = Path(self.path_prefix)
        if not resource_files_root_path.exists():
            resource_files_root_path.mkdir(parents=True)
        files = self.local_folder.get_contents_recursive(self.path_prefix, resource_files_root_path, LOCAL_PREFIX+':')
        root_dir = {
            "name": "",
            "path": LOCAL_PREFIX + ":/",
            "sizeBytes": self.local_folder.get_size(self.path_prefix),
            "modifiedTime": str(datetime.datetime.fromtimestamp(resource_files_root_path.stat().st_mtime)),
            "type": "folder",
            "contents": files,
        }
        return root_dir

    def update_hs_files(self):
        # TODO (Kyle): evaluate cache and remove if not used
        self.hs_files = self.get_files_upon_init_HS()

    def get_files_HS(self):
        return self.hs_files

    def get_files_upon_init_HS(self):
        """Gets metadata for all the files currently stored in the HS instance
        of this resource.
        """

        # TODO (Vicky) fix this function & break it out into multiple functions
        # get the file information for all files in the HS resource in json
        # TODO (Vicky): remove this?
        #print(self.hs.resource(self.res_id).files.all().json())
        # testing = (self.hs.getResourceFileList(self.res_id))
        # for test in testing:
        #     print("THIS IS A TEST")
        #     print(test)
        hs_resource_info = (self.hs.getResourceFileList(self.res_id))
        url_prefix = 'http://www.hydroshare.org/resource/' + self.res_id + '/data/contents'
        folders_dict = {}
        folders_final = []
        nested_files = {}
        # TODO: remove commented-out lines?
        try:
            # get the needed info for each file
            for file_info in hs_resource_info:
                # print(file_info)
                # extract filepath from url
                filepath = file_info["url"][len(url_prefix)+1:]
                # get proper definition formatting of file if it is a file
                file_definition_hs = self.remote_folder.get_file_metadata(filepath, filepath, file_info,
                                                                          HS_PREFIX+':')
                # if it is a folder, build up contents
                if not file_definition_hs:
                    nested_files[filepath + "/"] = file_info
                    folders = filepath.split("/")
                    currpath = ""
                    for x in range(0, len(folders)-1):
                        folder = folders[x]
                        currpath = currpath + folder + "/"
                        # build up dictionary of folder -> what is in it
                        if (x, folder, currpath) not in folders_dict:
                            folders_dict[(x, folder, currpath)] = []
                        folders_dict[(x, folder, currpath)].append((x+1, folders[x+1], currpath + folders[x+1] + "/"))
                # if it is just a file, add it to the final list
                else:
                    folders_final.append(file_definition_hs)
        except Exception as e:
            # TODO: get rid of this nonsense once things are working
            print(type(e))
            # print(e.url)
            # print(e.method)
            # print(e.status_code)
            # print(e.status_msg)


        # go through folders dictionary & build up the nested structure
        i = 0
        for key, val in folders_dict.items():
            # we only want to make the initial call on folders at the top level,
            # (level 0); folders at levels 1, 2, etc. will be built into the
            # result by means of the recursive calls
            if key[0] == 0:
                folder_time, folder_size, folder_contents = self.remote_folder.get_contents_recursive(val, folders_dict,
                                                                                         nested_files, HS_PREFIX+':')
                if folder_time:
                    folder_time = str(folder_time)
                # TODO (vicky): use name and path instead of key[i]
                folders_final.append({
                    "name": key[1],
                    "path": HS_PREFIX + ':/' + key[2].strip('/'),
                    "sizeBytes": folder_size,
                    "modifiedTime": folder_time,
                    "type": "folder",
                    "contents": folder_contents,
                })

        # TODO: probably add some comments explaining what these lines are doing
        rootsize = 0
        for f in folders_final:
            rootsize += (f["sizeBytes"])

        root_dir = {
            "name": "",
            "path": HS_PREFIX + ":/",
            "sizeBytes": rootsize,
            "modifiedTime": str(self.get_resource_last_modified_time_HS()),
            "type": "folder",
            "contents": folders_final,
        }

        return root_dir

    def rename_or_move_file_HS(self, src_path, dest_path):
        metadata = self.find_file_or_folder_metadata(src_path, self.hs_files["contents"])
        self.rename_or_move_file_HS_recursive(src_path, dest_path, src_path)
        # if the thing that was moved was a folder, remove it
        if metadata["type"] == "folder":
            self.hs.deleteResourceFolder(self.res_id, pathname=src_path)

    def rename_or_move_file_HS_recursive(self, src_path, dest_path, og_src):
        """Renames the hydroshare version of the file from old_filename to
        new_filename.
        """
        metadata = self.find_file_or_folder_metadata(src_path, self.hs_files["contents"])
        if metadata["type"] == "folder":
            for sub_dicts in metadata.get("contents"):
                new_src = self.remove_prefix(sub_dicts.get("path"), "hs:/")
                self.rename_or_move_file_HS_recursive(new_src, dest_path, og_src)

        else:
            # at this point we know source is referring to a file, not folder
            # get the source filename & path to source file
            if "/" in src_path:
                src_path_to_file, src_filename = src_path.rsplit("/", 1)
            else:
                src_filename = src_path
                src_path_to_file = None

            # find the most specific file or folder specified in original source
            # i.e. is it an upper level folder, a file, etc.
            if "/" in og_src:
                ignore_me, most_specific = og_src.rsplit("/", 1)
            else:
                most_specific = og_src
            # destination path should include whatever was specified in og_src
            # up until right before the src_filename
            idx = src_path.find(most_specific)
            end_idx = src_path.find(src_filename)

            # find out if you need a separator between dest_path & src_path
            # (you don't if dest_path is an empty string)
            if dest_path == "":
                dest_full_path = src_path[idx:end_idx-1]
                dest_plus_file = src_path[idx:]
                src_full_path = src_path
            else:
                if src_path[idx:end_idx] != "":
                    dest_full_path = dest_path + "/" + src_path[idx:end_idx-1]
                else:
                    dest_full_path = dest_path
                dest_plus_file = dest_path + "/" + src_path[idx:]
                src_full_path = src_path

            try:
                metadata = self.find_file_or_folder_metadata(dest_full_path, self.hs_files["contents"])
                if metadata is None and dest_full_path != "":
                    self.remote_folder.create_folder(dest_full_path)
            except Exception:
                self.remote_folder.create_folder(dest_full_path)

            # remove any existing copy of the file in its destination location
            if self.is_file_in_HS(dest_plus_file, self.hs_files["contents"]):
                self.delete_file_or_folder_from_HS(dest_plus_file)

            self.remote_folder.rename_or_move_file(src_full_path, dest_plus_file)
            self.hs_files = self.get_files_upon_init_HS()

    # TODO: probably remove and use is_file_or_folder_in_HS instead
    # or actually maybe remove the other one cause this seems simpler...
    def is_file_in_HS(self, filepath, files_info):
        """ does a file exist in hs_files """
        found = False

        for file_dict in files_info:
            if file_dict["type"] == "folder":
                found = found or self.is_file_in_HS(filepath, file_dict["contents"])
            else:
                # cut out the hs:/ at beginning of path in comparison
                if filepath == self.remove_prefix(file_dict["path"], "hs:/"):
                    return True

        return found

    def remove_prefix(self, text, prefix):
        if text.startswith(prefix):
            return text[len(prefix):]
        return text

    def remove_suffix(self, text, suffix):
        if not text.endswith(suffix):
            return text
        return text[:-len(suffix)]

    def rename_or_move_file_JH(self, old_filepath, new_filepath, full_paths=False):
        """Renames the jupyterhub version of the file from old_filename to
        new_filename.
        """
        # TODO: should probably throw an exception if this is not true
        if old_filepath is not None and new_filepath is not None:
            if not full_paths:
                src_full_path = self.path_prefix / old_filepath
                dest_full_path = self.path_prefix / new_filepath
            else:
                src_full_path = old_filepath
                dest_full_path = new_filepath
            if src_full_path.exists():
                shutil.move(str(src_full_path), str(dest_full_path))
            else:  # TODO: also an exception
                logging.info('Trying to rename or move file that does not exist: ' + str(old_filepath))
        else:
            logging.info('Missing inputs for old and new filepath')

    def delete_file_or_folder_from_JH(self, item_path):
        """ Deletes a file or folder from the local filesystem.
            :param item_path the full path to the file or folder on the local filesystem
            :type item_path str | PosixPath
        """
        # Remove any leading /
        if item_path.startswith('/'):
            item_path = item_path[1:]

        item_full_path = self.path_prefix / item_path

        if item_full_path.is_dir():
            self.local_folder.delete_folder(item_full_path)
            return 'folder'
        else:
            self.local_folder.delete_file(item_full_path)
            return 'file'

    # TODO: use 'exists' in this function name
    def is_file_or_folder_in_JH(self, filepath):
        """ is a file in JH """
        return path.exists(filepath)

    def delete_file_or_folder_from_HS(self, item_path):
        """ deletes file or folder from HS """
        return self.remote_folder.delete_file_or_folder(item_path)

    def delete_HS_folder_if_empty(self, folderpath, acceptable_name):
        """ deletes folder from HS if it is empty
        this can only be used with hs_files as the HydroShare API does not give us empty
        folders when giving us files. This function should only be used if a recent
        action could have caused a folder to be empty """
        # TODO: snake_case_please
        splitPath = ["/"]
        splitPath += folderpath.split('/')
        parentDict = self.hs_files
        for directory in splitPath:
            i = 0
            while i < len(parentDict):
                if parentDict[i]["name"] == directory:
                    parentDict = parentDict[i]["contents"]
                    break
                i += 1

        j = 0
        for i in range(len(parentDict)):
            if parentDict[i]["name"] != acceptable_name:
                j += 1
        if j == 0:
            self.delete_file_or_folder_from_HS(folderpath)

    # TODO: change name to include "exists"
    def is_file_or_folder_in_HS(self, item_path, file_extension=None):
        """ Checks if a file or folder exists in a HydroShare resource
            :param item_path the name (sans extension) of the file or folder
            :param file_extension if a file, the extension of that file
         """
        if not isinstance(item_path, PosixPath):
            item_path = Path(item_path)
        current_dir_contents = self.hs_files.get('contents')
        for current_path_part in item_path.parts:
            found_next_part = False
            for file_or_folder in current_dir_contents:
                if file_or_folder["name"] == current_path_part:
                    if file_or_folder["type"] == "folder":
                        current_dir_contents = file_or_folder.get('contents')
                        found_next_part = True
                        break
                    elif file_extension is not None and file_or_folder["type"] == file_extension:
                        return True
            if not found_next_part:
                return False

        return False

    def find_file_or_folder_metadata(self, path, metadata_dict):
        """ Recursively gets and returns the metadata dictionary that is
        nested within metadata dict for the file or folder at specified path.
        """
        if metadata_dict is None:
            raise Exception("File or folder not found.")
        if "/" in path:
            first_level, rest_of_path = path.split("/", 1)
            for dicts in metadata_dict:
                if dicts["name"] == first_level:
                    return self.find_file_or_folder_metadata(rest_of_path, dicts.get("contents"))
        else:
            for dicts in metadata_dict:
                name = dicts.get("name")
                if "." in path:
                    path_no_extension, extension = path.rsplit(".", 1)
                else:
                    path_no_extension = None
                if name == path or name == path_no_extension:
                    return dicts

    def overwrite_JH_with_file_from_HS(self, src_path, dest_path):
        # find a temp folder location that does not exist
        temp_location = "/temp/"
        i = 1
        while Path(self.remove_suffix(str(self.path_prefix), "/contents") + "/temp/").exists():
            temp_location = "/temp" + str(i) + "/"
            i += 1
        # recursively overwrite all nested files from src_path
        self.overwrite_JH_with_file_from_HS_recursive(src_path, dest_path, src_path, temp_location)
        # remove the temporary folder
        self.local_folder.delete_folder(self.remove_suffix(str(self.path_prefix), "/contents") + temp_location)

    def overwrite_JH_with_file_from_HS_recursive(self, src_path, dest_path, og_src, temp_location):
        """ Recursively overwrites JH files located at the specified dest_path
        with files from the given src_path in HS """
        metadata = self.find_file_or_folder_metadata(src_path, self.hs_files["contents"])
        if metadata["type"] == "folder":
            for sub_dicts in metadata.get("contents"):
                new_src = self.remove_prefix(sub_dicts.get("path"), "hs:/")
                self.overwrite_JH_with_file_from_HS_recursive(new_src, dest_path, og_src, temp_location)
        else:
            # at this point we know source is referring to a file, not folder
            # get the source filename & path to source file
            if "/" in src_path:
                src_path_to_file, src_filename = src_path.rsplit("/", 1)
            else:
                src_filename = src_path
                src_path_to_file = None

            # delete existing file at destination, if applicable
            if self.is_file_or_folder_in_JH(self.remove_suffix(str(self.path_prefix), "/contents") + temp_location + dest_path + src_path):
                self.local_folder.delete_file(self.remove_suffix(str(self.path_prefix), "/contents") + temp_location + dest_path + src_path)

            output_path = dest_path

            if src_path_to_file is not None:
                if output_path == "": output_path = src_path_to_file
                else: output_path = output_path + "/" + src_path_to_file

            if not (Path(self.remove_suffix(str(self.path_prefix), "/contents") + temp_location + output_path)).exists():
                # create local folders that lead to output_path if they don't exist
                os.makedirs(self.remove_suffix(str(self.path_prefix), "/contents") + temp_location + output_path + "/")

            self.remote_folder.download_file_to_JH(src_path, self.remove_suffix(str(self.path_prefix), "/contents") + temp_location + dest_path)

            # find the most specific file or folder specified in original source
            # i.e. is it an upper level folder, a file, etc.
            if "/" in og_src:
                ignore_me, most_specific = og_src.rsplit("/", 1)
            else:
                most_specific = og_src
            # destination path should include whatever was specified in og_src
            # up until right before the src_filename
            idx = src_path.find(most_specific)
            end_idx = src_path.find(src_filename)

            # find out if you need a separator between dest_path & src_path
            # (you don't if dest_path is an empty string)
            if dest_path == "":
                dest_full_path = Path(str(self.path_prefix) + "/" + src_path[idx:end_idx])
                src_full_path = Path(self.remove_suffix(str(self.path_prefix), "/contents") + temp_location + src_path)
            else:
                dest_full_path = Path(str(self.path_prefix) + "/" + dest_path + "/" + src_path[idx:end_idx])
                src_full_path = Path(self.remove_suffix(str(self.path_prefix), "/contents") + temp_location + dest_path + "/" + src_path)

            if not (dest_full_path).exists():
                # create local folders that lead to dest_full_path if they don't exist
                os.makedirs(str(dest_full_path) + "/")

            # remove any existing copy of the file in its destination location
            if Path(str(dest_full_path) + "/" + src_filename).exists():
                self.local_folder.delete_file(str(dest_full_path) + "/" + src_filename)

            # move the file to its proper location
            if src_full_path.exists():
                shutil.move(str(src_full_path), str(dest_full_path))

            # TODO (kyle): figure out what is going on here
            self.JH_files = self.get_files_upon_init_JH()

    def overwrite_HS_with_file_from_JH(self, src_path, dest_path):
        self.overwrite_HS_with_file_from_JH_recursive(src_path, dest_path, src_path)

    def overwrite_HS_with_file_from_JH_recursive(self, src_path, dest_path, og_src):
        """ overwrites HS file with one from JH """
        metadata = self.find_file_or_folder_metadata(src_path, self.JH_files["contents"])
        if metadata["type"] == "folder":
            for sub_dicts in metadata.get("contents"):
                new_src = self.remove_prefix(sub_dicts.get("path"), "local:/")
                self.overwrite_HS_with_file_from_JH_recursive(new_src, dest_path, og_src)

        else:
            # at this point we know source is referring to a file, not folder
            # get the source filename & path to source file
            if "/" in src_path:
                src_path_to_file, src_filename = src_path.rsplit("/", 1)
            else:
                src_filename = src_path
                src_path_to_file = None

            # find the most specific file or folder specified in original source
            # i.e. is it an upper level folder, a file, etc.
            if "/" in og_src:
                ignore_me, most_specific = og_src.rsplit("/", 1)
            else:
                most_specific = og_src
            # destination path should include whatever was specified in og_src
            # up until right before the src_filename
            idx = src_path.find(most_specific)
            end_idx = src_path.find(src_filename)

            # find out if you need a separator between dest_path & src_path
            # (you don't if dest_path is an empty string)
            if dest_path == "":
                dest_full_path = src_path[idx:end_idx-1]
                dest_plus_file = src_path[idx:]
                src_full_path = Path(str(self.path_prefix) + "/" + src_path)
            else:
                if src_path[idx:end_idx] != "":
                    dest_full_path = dest_path + "/" + src_path[idx:end_idx-1]
                else:
                    dest_full_path = dest_path
                dest_plus_file = dest_path + "/" + src_path[idx:]
                src_full_path = Path(str(self.path_prefix) + "/" + src_path)

            try:
                metadata = self.find_file_or_folder_metadata(dest_full_path, self.hs_files["contents"])
                if metadata is None and dest_full_path != "":
                    self.remote_folder.create_folder(dest_full_path)
            except Exception:
                self.remote_folder.create_folder(dest_full_path)

            # remove any existing copy of the file in its destination location
            if self.is_file_in_HS(dest_plus_file, self.hs_files["contents"]):
                self.delete_file_or_folder_from_HS(dest_plus_file)

            self.remote_folder.upload_file_to_HS(Path(src_full_path), Path(dest_plus_file))
            self.hs_files = self.get_files_upon_init_HS()

    def get_resource_last_modified_time_HS(self):
        """
        Gets dates from the resource science metadata and returns the
        most recent modified time in datetime.datetime format
        """
        metadata = self.hs.getScienceMetadata(self.res_id)
        # Obtain dates
        dates = []
        for date in metadata['dates']:
            if date['type'] == 'modified':
                modified_time = date['start_date']
        modified_time = parse(modified_time)
        return modified_time # datetime.datetime

    def upload_file_to_JH(self, file_info):
        if self.is_file_or_folder_in_JH(self.path_prefix+file_info["filename"]) == False:
            self.local_folder.upload_file_to_JH(file_info, self.path_prefix)
            return True
        else:
            # TODO (Kyle): throw an exception
            return "Error: a file " + file_info["filename"] +" already exists in JupyterHub at that location, cannot upload"
