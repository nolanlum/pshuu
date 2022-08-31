import React from 'react';
import { createRoot } from 'react-dom/client';

import InfiniteScroll from 'react-infinite-scroll-component';


const listPageSize = 25;

class UploadList extends React.PureComponent {
    constructor(props) {
        super(props);
        this.state = {
            page: 0,
            hasMore: true,
            files: {},
        };
    }

    componentDidMount() {
        const nextPage = this.props.atPage + 1;
        this.fetchData(nextPage, 0, nextPage * listPageSize);
    }

    fetchMoreData = () => {
        const nextPage = this.state.page + 1;
        const limit = listPageSize;
        const offset = listPageSize * this.state.page;

        this.fetchData(nextPage, limit, offset)
            .then(_ => {
                const newQuery = '?' + new URLSearchParams({page: nextPage});
                window.history.replaceState({}, '', window.location.pathname + newQuery)
            });
    }

    fetchData = (nextPage, offset, limit) => {
        const queryParams = {
            offset: offset,
            limit: limit,
        };

        return fetch(this.props.url + '&' + new URLSearchParams(queryParams))
            .then(res => res.json())
            .then(
                (result) => {
                    if (result.status !== 'pshuu~') {
                        alert("well poop.");
                    }

                    this.setState({
                        page: nextPage,
                        hasMore: Object.keys(result.files).length === limit,
                        files: {
                            ...this.state.files,
                            ...result.files,
                        },
                    });
                },
                (error) => {
                    alert("well poop.");
                }
            );
    }

    render() {
        const fileIds = Object.keys(this.state.files);
        const fileRows = fileIds
            .sort(function(a, b) {
                a = parseInt(a);
                b = parseInt(b);
                return +(a < b) || +(a === b) - 1;
            }).map(function(file_key) {
                var file = this.state.files[file_key];
                var dateTime = new Date(file.upload_time).toLocaleString();
                return (
                    <Upload key={file_key} url={file.url} filename={file.original_filename} upload_time={dateTime} />
                );
            }.bind(this));

        return (
            <InfiniteScroll
              dataLength={fileIds.length}
              next={this.fetchMoreData}
              hasMore={this.state.hasMore}
              loader={<h4 style={{ textAlign: 'center' }}>Loading...</h4>}
            >
              <table className="uploads-table">
                <thead>
                  <tr>
                    <td style={{ textAlign: 'left', minWidth: '68px' }}>&nbsp;</td>
                    <td style={{ width: '100%' }}>Filename</td>
                    <td style={{ minWidth: '10em' }}>Upload time</td>
                  </tr>
                </thead>
                <tbody>
                    {fileRows}
                </tbody>
              </table>
            </InfiniteScroll>
        );
    }
}

class Upload extends React.PureComponent {
    render() {
        const thumb_url = this.props.url + '?thumb';
        return (
            <tr>
                <td><img src={thumb_url} alt={this.props.filename} /></td>
                <td><a href={this.props.url}>{this.props.filename}</a></td>
                <td>{this.props.upload_time}</td>
            </tr>
        );
    }
}

const pageParam = Number.parseInt(new URLSearchParams(window.location.search).get('page'), 10);
const startingPage = !Number.isNaN(pageParam) && pageParam > -1 ? pageParam : 0;

const root = createRoot(document.getElementById('content'));
root.render(<UploadList url={list_url} atPage={startingPage} />);
