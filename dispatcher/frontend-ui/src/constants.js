import moment from 'moment'
import querystring from 'querystring'

function datetime(value) { // display a datetime in a standard format
  if (!value)
    return '';
  return moment(value).format("LLL");
}

function duration(diff) { // display a duration in a standard format
  return moment.duration(diff).locale("en").humanize();
}

function duration_between(start, end) { // display a duration between two datetimes
  let diff = moment(end).diff(start);
  return duration(diff);
}

function params_serializer(params) { // turn javascript params object into querystring
  return querystring.stringify(params);
}

function now() {
  return moment();
}

export default {
  zimfarm_webapi: window.environ.ZIMFARM_WEBAPI || process.env.ZIMFARM_WEBAPI || "https://api.farm.openzim.org/v1",
  zimfarm_logs_url:  window.environ.ZIMFARM_LOGS_URL || process.env.ZIMFARM_LOGS_URL || "https://logs.warehouse.farm.openzim.org",
  kiwix_download_url:  window.environ.KIWIX_DOWNLOAD_URL || process.env.KIWIX_DOWNLOAD_URL || "https://download.kiwix.org/zim",
  DEFAULT_CPU_SHARE: 1024,  // used to generate docker cpu-shares
  standardHTTPError: function(response) {
    let statuses = {
      // 1××: Informational
      100: "Continue",
      101: "Switching Protocols",
      102: "Processing",
      
      // 2××: Success
      200: "OK",
      201: "Created",
      202: "Accepted",
      203: "Non-authoritative Information",
      204: "No Content",
      205: "Reset Content",
      206: "Partial Content",
      207: "Multi-Status",
      208: "Already Reported",
      226: "IM Used",
      
      // 3××: Redirection
      300: "Multiple Choices",
      301: "Moved Permanently",
      302: "Found",
      303: "See Other",
      304: "Not Modified",
      305: "Use Proxy",
      307: "Temporary Redirect",
      308: "Permanent Redirect",
      
      // 4××: Client Error
      400: "Bad Request",
      401: "Unauthorized",
      402: "Payment Required",
      403: "Forbidden",
      404: "Not Found",
      405: "Method Not Allowed",
      406: "Not Acceptable",
      407: "Proxy Authentication Required",
      408: "Request Timeout",
      409: "Conflict",
      410: "Gone",
      411: "Length Required",
      412: "Precondition Failed",
      413: "Payload Too Large",
      414: "Request-URI Too Long",
      415: "Unsupported Media Type",
      416: "Requested Range Not Satisfiable",
      417: "Expectation Failed",
      418: "I'm a teapot",
      421: "Misdirected Request",
      422: "Unprocessable Entity",
      423: "Locked",
      424: "Failed Dependency",
      426: "Upgrade Required",
      428: "Precondition Required",
      429: "Too Many Requests",
      431: "Request Header Fields Too Large",
      444: "Connection Closed Without Response",
      451: "Unavailable For Legal Reasons",
      499: "Client Closed Request",
      
      //5××: Server Error
      500: "Internal Server Error",
      501: "Not Implemented",
      502: "Bad Gateway",
      503: "Service Unavailable",
      504: "Gateway Timeout",
      505: "HTTP Version Not Supported",
      506: "Variant Also Negotiates",
      507: "Insufficient Storage",
      508: "Loop Detected",
      510: "Not Extended",
      511: "Network Authentication Required",
      599: "Network Connect Timeout Error",
    };

    let status_text = response.statusText ? response.statusText : statuses[response.status];
    return response.status + ": " + status_text + ".";
  },
  datetime: datetime,
  duration: duration,
  duration_between: duration_between,
  params_serializer:params_serializer,
  now: now,
};
