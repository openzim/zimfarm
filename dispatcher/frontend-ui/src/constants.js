import moment from 'moment'
import filesize from 'filesize'
import querystring from 'querystring'

function format_dt(value) { // display a datetime in a standard format
  if (!value)
    return '';
  let mom = moment(value);
  return mom.isValid() ? mom.format("LLL") : value;
}

function format_duration(diff) { // display a duration in a standard format
  return moment.duration(diff).locale("en").humanize();
}

function format_duration_between(start, end) { // display a duration between two datetimes
  let diff = moment(end).diff(start);
  return format_duration(diff);
}

function from_now(value) {
  let mom = moment(value);
  return mom.isValid() ? mom.fromNow() : value;
}

function params_serializer(params) { // turn javascript params object into querystring
  return querystring.stringify(params);
}

function now() {
  return moment();
}

function image_human(config) {
  return config.image.name + ":" + config.image.tag;
}

function build_docker_command(name, config) {
  let mounts = ["-v", "/my-path:" + config.mount_point + ":rw"];
  let mem_params = ["--memory-swappiness", "0", "--memory", config.resources.memory];
  let cpu_params = ["--cpu-shares", config.resources.cpu * DEFAULT_CPU_SHARE];
  let docker_base = ["docker", "run"].concat(mounts).concat(["--name", config.task_name + "_" + name, "--detach"]).concat(cpu_params).concat(mem_params);
  let scraper_command = config.str_command;
  let args = docker_base.concat([image_human(config)]).concat([scraper_command]);
  return args.join(" ");
}

function trim_command(command, columns=79) {  // trim a string to espaced version (at most columns)

  let parts;
  if (typeof(command) == "object" && Object.isArray(command)) {
    parts = command.map(function(part) { return part.replace(/^--/, ""); });
    command = parts.join(" ");
  } else {
    parts = command.split(" --");
  }
  // don't bother if command is not that long
  if (command.length <= columns)
    return command;

  let sep = "\\\n";
  // first line is considered already filled with PS1 (35 chars)
  let lines = [];
  let line = "";
  parts.forEach(function (part) {
    part = "--" + part + " ";
    // current line and part won't fit. let's flush to new line
    if (line.length + part.length >= columns) {
      lines.push(line);
      line = "";
    }
    // part alone can't fit a line
    if (part.length >= columns) {
      let sublines = [];
      let part_remaining = part;
      while (part_remaining.length) {
        sublines.push(part_remaining.substr(0, columns));
        part_remaining = part_remaining.substr(columns);
      }
      // add lines from those subparts to main
      lines = lines.concat(sublines);
    }
    // if we can fit, add to current line
    if (line.length + part.length <= columns) {
      line += part;
    }
  });
  lines.push(line);

  // remove -- from beggining
  let first_line = lines[0];
  lines[0] = first_line.substr(2);
  // remove extra space at end
  let last_line = lines[lines.length - 1];
  lines[lines.length - 1] = last_line.substr(0, last_line.length -1);

  let new_command = lines.join(sep);
  return new_command;
}

function short_id(id) {  // short id of tasks (last chars)
  return id.substr(id.length - 5);
}

function filesize2(value) {
  if (!value)
    return '';
  return filesize(value);
}

function duplicate(dict) {
  return JSON.parse(JSON.stringify(dict));
}


function schedule_durations_dict(duration) {
  function single_duration(value, worker, on) {
    return {single: true,
            value: value * 1000,
            worker: worker,
            on: on};
  }

  function multiple_durations(min_value, max_value, workers) {
    let min_workers = Object.values(Object.filter(workers, function (item) { return item.value == min_value; }));
    let max_workers = Object.values(Object.filter(workers, function (item) { return item.value == max_value; }));
    return {single: false,
            min_value: min_value * 1000,
            max_value: max_value * 1000,
            min_workers: min_workers,
            max_workers: max_workers};
  }

  if (!duration.available) {
    return single_duration(duration.default.value, "default", duration.default.on);
  }
  let min_worker = Object.min(duration.workers, 'value');
  let max_worker = Object.max(duration.workers, 'value');

  if (min_worker == max_worker) {
    return single_duration(duration.workers[min_worker].value, min_worker, duration.workers[min_worker].on);
  }
  let min_value = duration.workers[min_worker].value;
  let max_value = duration.workers[max_worker].value;
  return multiple_durations(min_value, max_value, duration.workers);
}

var DEFAULT_CPU_SHARE = 1024;

var ZIMFARM_WEBAPI = window.environ.ZIMFARM_WEBAPI || process.env.ZIMFARM_WEBAPI || "https://api.farm.openzim.org/v1";
var ZIMFARM_LOGS_URL = window.environ.ZIMFARM_LOGS_URL || process.env.ZIMFARM_LOGS_URL || "https://logs.warehouse.farm.openzim.org";
var cancelable_statuses = ["reserved", "started", "scraper_started", "scraper_completed", "scraper_killed"];
var running_statuses = cancelable_statuses.concat(["cancel_requested"]);

export default {
  isProduction() {
    return ZIMFARM_WEBAPI.indexOf("https://") == 0;
  },
  zimfarm_webapi: ZIMFARM_WEBAPI,
  zimfarm_logs_url:  ZIMFARM_LOGS_URL,
  kiwix_download_url:  window.environ.KIWIX_DOWNLOAD_URL || process.env.KIWIX_DOWNLOAD_URL || "https://download.kiwix.org/zim",
  DEFAULT_CPU_SHARE: DEFAULT_CPU_SHARE,  // used to generate docker cpu-shares
  DEFAULT_FIRE_PRIORITY: 5,
  DEFAULT_LIMIT: 20,
  LIMIT_CHOICES: [10, 20, 50, 100, 200],
  MAX_SCHEDULES_IN_SELECTION_REQUEST: 200,
  ALERT_DEFAULT_DURATION: 5,
  ALERT_LONG_DURATION: 10,
  ALERT_PERMANENT_DURATION: true,
  ROLES: ["editor", "manager", "admin", "worker", "processor"],
  TOKEN_COOKIE_EXPIRY: '180D',  // 6 months
  TOKEN_COOKIE_NAME: "auth",
  cancelable_statuses: cancelable_statuses,
  running_statuses: running_statuses,
  contact_email: "contact@kiwix.org",
  categories: ["gutenberg", "other", "phet", "psiram", "stack_exchange",
               "ted", "vikidia", "wikibooks", "wikinews", "wikipedia",
               "wikiquote", "wikisource", "wikispecies", "wikiversity",
               "wikivoyage", "wiktionary"],  // list of categories for fileering
  warehouse_paths: ["/gutenberg", "/other", "/phet", "/psiram", "/stack_exchange",
                    "/ted", "/vikidia", "/wikibooks", "/wikinews", "/wikipedia",
                    "/wikiquote", "/wikisource", "/wikispecies", "/wikiversity",
                    "/wikivoyage", "/wiktionary"],
  offliners: ["mwoffliner", "youtube", "phet", "gutenberg", "sotoki"],
  periodicities: ["manually", "monthly", "quarterly", "biannualy", "annually"],
  memory_values: [536870912, // 512MiB
                  1073741824,  // 1GiB
                  2147483648,  // 2GiB
                  3221225472,  // 3GiB
                  4294967296,  // 4GiB
                  5368709120,  // 5GiB
                  6442450944,  // 6GiB
                  7516192768,  // 7GiB
                  8589934592,  // 8GiB
                  9663676416,  // 9GiB
                  10737418240,  // 10GiB
                  11811160064,  // 11GiB
                  12884901888,  // 12GiB
                  13958643712,  // 13GiB
                  15032385536,  // 14GiB
                  16106127360,  // 15GiB
                  17179869184,  // 16GiB
                  34359738368,  // 32GiB
                  ],
  disk_values: [536870912, // 512MiB
                1073741824,  // 1GiB
                2147483648,  // 2GiB
                3221225472,  // 3GiB
                4294967296,  // 4GiB
                5368709120,  // 5GiB
                10737418240, // 10GiB
                16106127360,  // 15GiB
                21474836480,  // 20GiB
                32212254720,  // 30GiB
                42949672960,  // 40GiB
                53687091200,  // 50GiB
                80530636800,  // 75GiB
                107374182400,  // 100GiB
                134217728000,  // 125GiB
                161061273600,  // 150GiB
                214748364800,  // 200GiB
                268435456000,  // 250GiB
                ],
  yes_no(value, value_yes, value_no) {
    if (!value_yes)
      value_yes = "yes";
    if (!value_no)
      value_no = "no";
    return value ? value_yes : value_no;
  },
  standardHTTPError(response) {
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

    if (response === undefined) { // no response
                                  //usually due to browser blocking failed OPTION preflight request
      return "Cross-Origin Request Blocked: preflight request failed."
    }
    let status_text = response.statusText ? response.statusText : statuses[response.status];
    if (response.status == 400) {
      if (response.data && response.data.error)
        status_text += "<br />" + JSON.stringify(response.data.error);
      if (response.data && response.data.error_description)
        status_text += "<br />" + JSON.stringify(response.data.error_description);
      if (response.data && response.data.message)
        status_text += "<br />" + JSON.stringify(response.data.message);
    }
    return response.status + ": " + status_text + ".";
  },
  format_dt: format_dt,
  format_duration: format_duration,
  format_duration_between: format_duration_between,
  params_serializer:params_serializer,
  now: now,
  image_human: image_human,
  build_docker_command: build_docker_command,
  trim_command: trim_command,
  from_now: from_now,
  short_id: short_id,
  filesize: filesize2,
  duplicate: duplicate,
  schedule_durations_dict: schedule_durations_dict,
};
