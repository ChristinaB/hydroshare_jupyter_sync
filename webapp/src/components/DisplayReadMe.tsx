import * as React from 'react';
//import ReactMarkdown from 'react-markdown';

import '../styles/DisplayReadMe.scss';

export interface IPropTypes {
  jupyterHubReadMe?: string
}

export default class DisplayReadMe extends React.Component<IPropTypes, never> {

  public render() {
    const {
      jupyterHubReadMe,
    } = this.props;
     // const hydroShareUrl = `https://www.hydroshare.org/resource/${id}/`;
    const jhReadMe = jupyterHubReadMe ? (
        <div className="resource-info">
          {/* <p>{jupyterHubReadMe}</p> */}
            {/* <ReactMarkdown source={jupyterHubReadMe} /> */}
            {/* <div className="info-wrapping">
                <div className="info-group">
                    <span className="info-header">Author</span>
                    <p>{jupyterHubReadMe}</p>
                </div>
                <div className="info-group">
                    <span className="info-header">Owners</span>
                    <p>{hydroShareResource.authors}</p>
                </div>
                <div className="info-group">
                    <span className="info-header">Resource Type</span>
                    <p>{hydroShareResource.resource_type}</p>
                </div>
                <div className="info-group">
                    <span className="info-header">Created</span>
                    <p>{hydroShareResource.date_created}</p>
                </div>
                <div className="info-group">
                    <span className="info-header">Sharing Status</span>
                    <p>{hydroShareResource.status}</p>
                </div>
                <div className="info-group">
                    <span className="info-header">Last Modified</span>
                    <p>{hydroShareResource.date_last_updated.format('MMM D, YYYY H:mm a')}</p>
                </div>
            </div>
            <div className="info-group">
                <span className="info-header">Abstract</span>
                
            </div> */}
        </div>
    ) : null;
    return (
      <div className="ResourceInfo content-row tile">
        <div className="resource-meta-container">
          {jhReadMe}
        </div>
      </div>
    )
  }

}
