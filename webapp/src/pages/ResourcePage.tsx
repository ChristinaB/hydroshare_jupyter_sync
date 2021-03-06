import * as React from 'react';
import { connect } from 'react-redux';
import { ThunkDispatch } from "redux-thunk";
import { push } from 'connected-react-router';

import '../styles/ResourcePage.scss';

import FileManager from "../components/FileManager";
import Loading from "../components/Loading";
import Modal, {TextInput} from "../components/modals/Modal";
import NewFileModal from "../components/modals/NewFileModal";
import EditPrivacyModal from "../components/modals/EditPrivacyModal";
import ResourceMetadata from '../components/ResourceMetadata';
import ArchiveMessage from '../components/ArchiveMessage';
import ReadMeDisplay from '../components/ReadMeDisplay';
import UploadFileModal from '../components/modals/UploadFileModal';


import * as resourcesActions from '../store/actions/resources';
import {
  createNewFileOrFolder,
  copyFileOrFolder,
  deleteResourceFilesOrFolders,
  moveFileOrFolder,
  uploadNewFile,
  renameFileOrFolder,
} from '../store/async-actions';
import {
  IFile,
  IFolder,
  IResource,
  IRootState,
} from '../store/types';

const mapStateToProps = ({ resources, router }: IRootState) => {
  // Extract the resource ID from the URL
  // @ts-ignore object possibly undefined
  const regexMatch = router.location.pathname.split('/').pop().match(/^\w+/);
  let resourceForPage;
  let resourceId = undefined;
  if (regexMatch) {
    resourceId = regexMatch.pop() as string;
    if (resourceId) {
      resourceForPage = resources.allResources[resourceId]
    } else {
      return;
    }
  }
  const archiveMessage = resources.archiveMessage
  return {
    fetchingHydroShareFiles: resourceId ? resources.resourceHydroShareFilesBeingFetched.has(resourceId) : false,
    fetchingLocalFiles: resourceId ? resources.resourceLocalFilesBeingFetched.has(resourceId) : false,
    fetchingResourceMetadata: resources.fetchingResources,
    resource: resourceForPage,
    archiveMessage: archiveMessage,
  };
};

const mapDispatchToProps = (dispatch: ThunkDispatch<{}, {}, any>) => {
  return {
    createNewFile: (resource: IResource, filename: string, type: string) => dispatch(createNewFileOrFolder(resource, filename, type)),
    deleteResourceFilesOrFolders: (resource: IResource, paths: string[]) => dispatch(deleteResourceFilesOrFolders(resource, paths)),
    getFilesIfNeeded: (resource: IResource) => dispatch(resourcesActions.getFilesIfNeeded(resource)),
    openFile: (resource: IResource, file: IFile | IFolder) => dispatch(resourcesActions.openFileInJupyter(resource, file)),
    copyFileOrFolder: (resource: IResource, file: IFile, destination: IFolder) => dispatch(copyFileOrFolder(resource, file, destination)),
    moveFileOrFolder: (resource: IResource, file: IFile, destination: IFolder) => dispatch(moveFileOrFolder(resource, file, destination)),
    uploadNewFile: (resource: IResource, file: FormData) => dispatch(uploadNewFile(resource, file)),
    renameFileOrFolder: (resource: IResource, srcPath: string, destPath: string) => dispatch(renameFileOrFolder(resource, srcPath, destPath)),
    goBackToResources: () => dispatch(push('/')),
  }
};

type PropsType = ReturnType<typeof mapStateToProps> & ReturnType<typeof mapDispatchToProps>;

type StateType = {
  filesOrFoldersToConfirmDeleting: string[] | undefined
  modal: MODAL_TYPES,
  selectedFileToUpload: any,
  selectedFileToRename: IFile | IFolder | null,
};

class ResourcePage extends React.Component<PropsType, StateType> {

  state: StateType = {
    filesOrFoldersToConfirmDeleting: undefined,
    modal: MODAL_TYPES.NONE,
    selectedFileToUpload: null,
    selectedFileToRename: null,
  };

  displayModal = (type: MODAL_TYPES) => this.setState({modal: type});

  displayDeleteConfirmationModal = (paths: string[]) => this.setState({
    modal: MODAL_TYPES.DELETE,
    filesOrFoldersToConfirmDeleting: paths,
  });

  doDeleteSelectedFiles = () => {
    this.props.deleteResourceFilesOrFolders(this.props.resource!, this.state.filesOrFoldersToConfirmDeleting!);
    this.setState({
      filesOrFoldersToConfirmDeleting: undefined,
      modal: MODAL_TYPES.NONE,
    });
  };

  hideModal = () => this.setState({modal: MODAL_TYPES.NONE});

  public render() {
    const {
      fetchingHydroShareFiles,
      fetchingLocalFiles,
      fetchingResourceMetadata,
      resource,
    } = this.props;

    if (fetchingResourceMetadata) {
      return (
        <div className="page resource-details">
          <Loading/>
        </div>
      );
    }

    if (!resource) {
      return (
        <div className="page resource-details">
          <div className="no-resource">
            <h1>No resource found</h1>
            <p>You do not have a resource with the ID specified.</p>
          </div>
        </div>
      );
    }

    this.props.getFilesIfNeeded(resource);

    // const toggleAllLocalSelected = () => this.props.toggleSelectedAllLocal(resource!);
    // const toggleAllHydroShareSelected = () => this.props.toggleSelectedAllHydroShare(resource!);

    const copyFileOrFolder = (f: IFile | IFolder, dest: IFolder) => {
      this.props.copyFileOrFolder(resource, f, dest);
    };

    const moveFileOrFolder = (f: IFile | IFolder, dest: IFolder) => {
      this.props.moveFileOrFolder(resource, f, dest);
    };

    const createNewFile = (filename: string, type: string) => {
      this.props.createNewFile(resource, filename, type);
      this.setState({modal: MODAL_TYPES.NONE});
    };

    const editPrivacy = () => {
      window.location.replace(`https://www.hydroshare.org/resource/${resource.id}/`)
      this.setState({modal: MODAL_TYPES.NONE});
    };

    const onSelectedFileToUploadChange = (event: any) => {
      this.setState({selectedFileToUpload: event.target.files[0]})
    };

    const uploadFile = (file: any) => {
      const formData = new FormData();
      formData.append('file', this.state.selectedFileToUpload);
      this.props.uploadNewFile(this.props.resource!, formData);
    };

    const displayRenameHydroShareFileModal = (fileOrFolder: IFile | IFolder) => {
      this.setState({modal: MODAL_TYPES.RENAME_HYDROSHARE_FILE,
                    selectedFileToRename: fileOrFolder})
    }

    const displayRenameWorkspaceFileModal = (fileOrFolder: IFile | IFolder) => {
      this.setState({modal: MODAL_TYPES.RENAME_WORKSPACE_FILE,
                    selectedFileToRename: fileOrFolder})
    }

    const renameFileOrFolder = (item: IFile | IFolder, newName: string) => {
      const destPath = item.path.replace( item.name, newName)
      console.log(destPath)
      this.props.renameFileOrFolder(this.props.resource!, item.path, destPath)
    }

    const openFile = (file: IFile) => this.props.openFile(resource, file);

    let modal;

    switch (this.state.modal) {
      case MODAL_TYPES.NEW:
        modal = <NewFileModal close={this.hideModal} submit={createNewFile}/>;
        break;
      case MODAL_TYPES.DELETE:
        modal = <DeleteConfirmationModal
          close={this.hideModal}
          submit={this.doDeleteSelectedFiles}
          paths={this.state.filesOrFoldersToConfirmDeleting!}
        />;
        break;
      case MODAL_TYPES.EDIT_PRIVACY:
        modal = <EditPrivacyModal 
          close = {this.hideModal}
          submit = {editPrivacy}
        />;
        break
      case MODAL_TYPES.UPLOAD_FILE:
        modal = <UploadFileModal
          close = {this.hideModal}
          submit = {uploadFile}
          onFileChange = {onSelectedFileToUploadChange}
        />
        break
      case MODAL_TYPES.RENAME_HYDROSHARE_FILE:
        modal = <RenameFileModal 
          close = {this.hideModal}
          submit = {renameFileOrFolder}
          fileOrFolder = {this.state.selectedFileToRename}
          renameLocation = {"HydroShare"}
          />
        break
      case MODAL_TYPES.RENAME_WORKSPACE_FILE:
        modal = <RenameFileModal 
          close = {this.hideModal}
          submit = {renameFileOrFolder}
          fileOrFolder = {this.state.selectedFileToRename}
          renameLocation = {"Workspace"}
          />
        break
    }

    return (
      <div className="page resource-details">
        <ResourceMetadata 
          resource={resource} 
          promptEditPrivacy={() => this.displayModal(MODAL_TYPES.EDIT_PRIVACY)}/>
        {this.props.archiveMessage !== "" ? <ArchiveMessage message={this.props.archiveMessage}/> : <div></div>}
        <FileManager
          fetchingHydroShareFiles={fetchingHydroShareFiles}
          fetchingLocalFiles={fetchingLocalFiles}
          hydroShareResourceRootDir={resource.hydroShareFiles}
          localFilesRootDir={resource.localFiles}
          openFile={openFile}
          copyFileOrFolder={copyFileOrFolder}
          moveFileOrFolder={moveFileOrFolder}
          promptCreateNewFileOrFolder={() => this.displayModal(MODAL_TYPES.NEW)}
          promptDeleteFilesOrFolders={this.displayDeleteConfirmationModal}
          promptUploadFile = {() => this.displayModal(MODAL_TYPES.UPLOAD_FILE)}
          promptRenameFileOrFolderHydroShare = {displayRenameHydroShareFileModal}
          promptRenameFileOrFolderWorkspace= {displayRenameWorkspaceFileModal}
          resourceId={resource.id}
        />
        <ReadMeDisplay localReadMe={this.props.resource? this.props.resource.localReadMe : "# No ReadMe yet"} resId={resource.id}/>
        {modal}
      </div>
    )
  }

}

enum MODAL_TYPES {
  NONE,
  NEW,
  DELETE,
  EDIT_PRIVACY,
  UPLOAD_FILE,
  RENAME_HYDROSHARE_FILE,
  RENAME_WORKSPACE_FILE,
}

type DeleteConfirmationModalProps = {
  close: () => any
  submit: () => any
  paths: string[]
};

const DeleteConfirmationModal: React.FC<DeleteConfirmationModalProps> = (props: DeleteConfirmationModalProps) => {
  // Remove the prefix (i.e. hs: or local:) from each path
  const pathsCleaned = props.paths.map(p => p.split(':')[1]);
  const count = pathsCleaned.length;
  const message = `Are you sure you want to delete the following ${count} item${count === 1 ? '' : 's'}?`;
  return (
    <Modal
      close={props.close}
      title="Confirm Deletion"
      submit={props.submit}
      isValid={true}
      submitText="Delete"
      isWarning={true}
    >
      <p>{message}</p>
      {pathsCleaned.map(p => <p>{p}</p>)}
    </Modal>
  );
};

type RenameFileModalProps = {
  close: () => any
  submit: (item: IFile | IFolder, destPath: string) => any
  fileOrFolder: IFile | IFolder |null
  renameLocation: string
};

const RenameFileModal: React.FC<RenameFileModalProps> = (props: RenameFileModalProps) => {
  const [state, setState] = React.useState({
    renameTextField: props.fileOrFolder!.name,
  });
  // Remove the prefix (i.e. hs: or local:) from each path
  const disable = props.renameLocation === "HydroShare" && props.fileOrFolder?.type === "folder";
  
  const handleChange = (renameTextField: string) => setState({renameTextField});
  const renameFile = () => {
    props.submit(props.fileOrFolder!, state.renameTextField);
    props.close();
  };

  let content = disable ? (
    <p>To rename a HydroShare folder, please click the "Open in HydroShare" button and rename the folder there.</p>
  ) : (
    <TextInput onChange={handleChange} value={state.renameTextField} title="Rename file" />
  );

  const isValid = !disable && state.renameTextField.length > 0;

  return (
    <Modal
      close={props.close}
      title="Rename file or folder"
      submit={renameFile}
      isValid={isValid}
      submitText="Rename"
      isConfirm={true}
    >
      {content}
    </Modal>
  );
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(ResourcePage);
