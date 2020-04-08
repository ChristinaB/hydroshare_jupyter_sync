import * as React from 'react';
import {
  IJupyterResource,
} from '../store/types';

import '../styles/ResourceMetadata.scss';

export interface IPropTypes {
  resource: IJupyterResource
}

export default class ResourceMetadata extends React.Component<IPropTypes, never> {

  public render() {
    const {
     // id,
      title,
      hydroShareResource,
    } = this.props.resource;
     // const hydroShareUrl = `https://www.hydroshare.org/resource/${id}/`;
    const hsResourceMeta = hydroShareResource ? (
        <div className="resource-info">
            <div className="info-wrapping">
                <div className="info-group">
                    <span className="info-header">Author</span>
                    <p>{hydroShareResource.author}</p>
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
                    <span className="info-header">Last Modified</span>
                    <p>{hydroShareResource.date_last_updated.format('MMM D, YYYY')}</p>
                </div>
                <div className="info-group">
                    <span className="info-header">Sharing Status</span>
                    <p>{hydroShareResource.status}</p>
                </div>
            </div>
            <div className="info-group">
                <span className="info-header">Abstract</span>
                <p>{hydroShareResource.abstract}</p>
            </div>
        </div>
    ) : null;
    return (
      <div className="ResourceInfo content-row tile">
        <h1 className="title">{title}</h1>
        <div className="resource-meta-container">
          {hsResourceMeta}
        </div>
      </div>
    )
  }

}
