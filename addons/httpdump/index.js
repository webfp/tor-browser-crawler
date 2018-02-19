let { Cc, Ci, Cu, Cr } = require('chrome');
const observerService = Cc["@mozilla.org/observer-service;1"].
                                                getService(Ci.nsIObserverService);
const URL = "https://tablog-webfpext.rhcloud.com/getsize.php";
const Request = require("sdk/request").Request;
const { NetUtil } = Cu.import("resource://gre/modules/NetUtil.jsm", {});

// Dumping data to disk
// --------------------------------------
const file = Cc["@mozilla.org/file/directory_service;1"]
                         .getService(Ci.nsIProperties).get("TmpD", Ci.nsIFile);
file.append("tbb-http.log");

// create component for file writing
if (file.exists() == false) {  // check to see if file exists
    file.create(Ci.nsIFile.NORMAL_FILE_TYPE, 420);
}

function writelog(data_array) {
		var sep = '\t';
        var foStream = Cc["@mozilla.org/network/file-output-stream;1"].
                                   createInstance(Ci.nsIFileOutputStream);
        foStream.init(file, 0x02 | 0x10, 0666, 0);
        var converter = Cc["@mozilla.org/intl/converter-output-stream;1"].
                                   createInstance(Ci.nsIConverterOutputStream);
        converter.init(foStream, "UTF-8", 0, 0);
        converter.writeString(data_array.join(sep) + '\n');
        converter.close(); // this closes foStream
}

function get_str(headers) {
	var headersObject = new Object();
	for (var key in headers) {
		if (headers.hasOwnProperty(key)) {
			headersObject[key] = headers[key];
            // arr_headers.push(key + ':' + headers[key]);
		}
	}
	return JSON.stringify(headersObject);
	// return JSON.stringify(headers);
}

function get_ts() {
	var d = new Date();
	var ts = d.getTime();
	return ts;
}

// delay the execution of a function
var delayedFunction = function(delay, fun) {
    var timer = Cc["@mozilla.org/timer;1"].createInstance(Ci.nsITimer);
    timer.initWithCallback({
        notify: function(timer) {
            fun();
        }
    }, delay, Ci.nsITimer.TYPE_ONE_SHOT);
}



// wtrite header
writelog(['msgType', 'method', 'version', 'totalLength', 'timestamp' , 'url', 'headers']);
// --------------------------------------

var getRequestHeaderLength = function(httpChannel) {
	var headerLength = 0;
	httpChannel.visitRequestHeaders(function(header, value) {
		headerLength += header.length + ": ".length + value.length + "\r\n".length;
	});
	return headerLength;
}

var getResponseHeaderLength = function(httpChannel) {
	var headerLength = 0;
	httpChannel.visitResponseHeaders(function(header, value) {
		headerLength += header.length + ": ".length + value.length + "\r\n".length;
	});
	return headerLength;
}


var httpObserver = {
    observe: function(aSubject, aTopic, aData) {
        var httpChannel = aSubject.QueryInterface(Ci.nsIHttpChannel);
		var headerLength = getRequestHeaderLength(httpChannel);
		var contentLength = 0;
        var visitor = new HeaderInfoVisitor(aSubject);
        if (aTopic == "http-on-modify-request") {
            // suspend request and schedule resume after a number
            // between 0 and 1 seconds.
            // Drop connections to https://check.torproject.org that comes from TorButton and/or HTTPSEverywhere 
            if (aSubject.URI.asciiSpec.indexOf("https://check.torproject.org/?TorButton=true") != -1){
                httpChannel.cancel(Cr.NS_BINDING_ABORTED);
                return;
            }
			delayedFunction(0, function() {
				if (aSubject instanceof Ci.nsIRequest) { // Is this needed?
					// add url for this domain
					if (aSubject.URI instanceof Ci.nsIURI) { // check it's a URI
						if (aSubject.requestMethod === 'POST') {
							aSubject.QueryInterface(Ci.nsIUploadChannel);
							var postData = aSubject.uploadStream;
							if(postData){
								postData.QueryInterface(Ci.nsISeekableStream).seek(Ci.nsISeekableStream.NS_SEEK_SET, 0);
								contentLength = postData.available();
								//let data = NetUtil.readInputStreamToString(postData, postData.available())
							}
						}
						var totalLength = headerLength + contentLength;
						var requestHeaders = visitor.visitRequest();
						var domain = aSubject.URI.host;
						var url = aSubject.URI.spec;
						writelog(['REQUEST', aSubject.requestMethod, 'NA', totalLength, get_ts(), url, get_str(requestHeaders)]);
					}
				}
			});
        } else if (aTopic == "http-on-examine-response") {
            // fire another request after this response?
            // probSendRequest();
			delayedFunction(0, function() {
				var url = aSubject.URI.asciiSpec;
				var responseHeaders = visitor.visitResponse();
				contentLength = responseHeaders['Content-Length'] || 0;
				var headerLength = getResponseHeaderLength(httpChannel);
				var totalLength = headerLength + parseInt(contentLength, 10);
				writelog(['RESPONSE', 'NA', 'NA', totalLength, get_ts(), url, get_str(responseHeaders)]);
			});
        }
    },
};

function HeaderInfoVisitor(oHttp) {
    this.oHttp = oHttp;
    this.headers = new Array();
}

HeaderInfoVisitor.prototype = {
    visitHeader: function(name, value) {
        this.headers[name] = value;
    },
    visitRequest: function() {
        this.oHttp.visitRequestHeaders(this);
        return this.headers;
    },
    visitResponse: function() {
        this.oHttp.visitResponseHeaders(this);
        return this.headers;
    }
};

observerService.addObserver(httpObserver, "http-on-modify-request", false);
observerService.addObserver(httpObserver, "http-on-examine-response", false);

