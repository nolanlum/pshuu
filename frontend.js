var UploadList = React.createClass({
    getInitialState: function() {
        return {
            'files': {}
        };
    },

    componentDidMount: function() {
        this.serverRequest = $.get(this.props.url, function (result) {
            if (result.status !== "pshuu~") {
                alert("well poop.");
            }

            this.setState({
                files: result.files
            });
        }.bind(this));
    },

    componentWillUnmount: function() {
        this.serverRequest.abort();
    },

    render: function() {
        var fileRows = Object
            .keys(this.state.files)
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
        );
    }
});

var Upload = React.createClass({
    getInitialState: function() {
        return {
            selected: false
        };
    },

    render: function() {
        var thumb_url = this.props.url + "?thumb";
        return (
            <tr>
                <td><img src={thumb_url} alt={this.props.filename} /></td>
                <td><a href={this.props.url}>{this.props.filename}</a></td>
                <td>{this.props.upload_time}</td>
            </tr>
        );
    }
});

ReactDOM.render(
    <UploadList url={list_url} />,
    document.getElementById('content')
);