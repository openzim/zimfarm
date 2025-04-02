import { filesize } from "filesize";
import querystring from "querystring";
const { DateTime, Duration, Interval } = require("luxon");

function isFirefoxOnIOS() {
  let ua = navigator.userAgent.toLowerCase();
  return (
    ua.indexOf("mobile") >= 0 &&
    ua.indexOf("mozilla") >= 0 &&
    ua.indexOf("applewebkit") >= 0
  );
}

function format_dt(value) {
  // display a datetime in a standard format
  if (!value) return "";
  let dt = DateTime.fromISO(value);
  if (dt.invalid) return value;
  return dt.toFormat("fff");
}

function to_timestamp(value) {
  if (!value) return 0;
  let dt = DateTime.fromISO(value);
  if (dt.invalid) return 0;
  return dt.toMillis();
}

function get_units(interval) {
  let units = [];
  let all_units = ["months", "days", "hours", "minutes"];
  all_units.forEach(function (unit) {
    if (interval.length(unit) >= 1) units.push(unit);
  });
  if (units.length == 0) units.push("seconds");
  return units;
}

function to_duration_obj(milliseconds) {
  var items = {
    years: 0,
    months: 0,
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
    milliseconds: milliseconds,
  };

  function to_obj() {
    let o = {};
    Object.entries(items).forEach((item) => {
      let [key, value] = item;
      if (value >= 1 && key != "milliseconds") o[key] = value;
    });
    return o;
  }

  function shift(lower, upper, num) {
    items[upper] = items[lower] / num;
    items[lower] = items[lower] % num;
    return items[upper] < 1;
  }
  if (shift("milliseconds", "seconds", 1000)) return to_obj();
  if (shift("seconds", "minutes", 60)) return to_obj();
  if (shift("minutes", "hours", 60)) return to_obj();
  if (shift("hours", "days", 24)) return to_obj();
  if (shift("days", "months", 30)) return to_obj();
  shift("months", "years", 12);
  return to_obj();
}

function format_duration(duration_value) {
  let dur = Duration.fromObject(to_duration_obj(duration_value));
  return dur.toHuman({ maximumSignificantDigits: 1 });
}

function format_duration_between(start, end) {
  // display a duration between two datetimes
  var int = Interval.fromDateTimes(
    DateTime.fromISO(start),
    DateTime.fromISO(end)
  );
  let diff = Duration.fromObject(int.toDuration(get_units(int)).toObject());
  return diff.toHuman({ maximumSignificantDigits: 1 });
}

function from_now(value) {
  if (!value) return "";
  let start = DateTime.fromISO(value);
  if (start.invalid) return value;
  return start.toRelative();
}

function params_serializer(params) {
  // turn javascript params object into querystring
  return querystring.stringify(params);
}

function now() {
  return DateTime.now();
}

function image_human(config) {
  return config.image.name + ":" + config.image.tag;
}

function image_url(config) {
  let prefix =
    config.image.name.indexOf("ghcr.io") != -1
      ? "https://"
      : "https://hub.docker.com/r/";
  return prefix + config.image.name;
}

function logs_url(task) {
  return upload_url(task.upload.logs.upload_uri, task.container.log);
}

function artifacts_url(task) {
  return upload_url(task.upload.artifacts.upload_uri, task.container.artifacts);
}

function upload_url(uri, filename) {
  let url = new URL(uri);
  let scheme = url.protocol.replace(/:$/, "");

  if (["http", "https"].indexOf(scheme) == -1)
    url = new URL(url.href.replace(new RegExp("^" + url.protocol), "https:"));

  if (scheme == "s3") {
    let log_url = url.protocol + "//" + url.host + url.pathname;
    let bucketName = url.searchParams.get("bucketName");
    if (bucketName) log_url += bucketName + "/";
    return log_url + filename;
  }

  return filename;
}

function build_command_without(config, secret_fields) {
  if (secret_fields == null) return "<missing defs>";

  return config.str_command;
}

function build_docker_command(name, config, secret_fields) {
  let mounts = ["-v", "/my-path:" + config.mount_point + ":rw"];
  let mem_params = [
    "--memory-swappiness",
    "0",
    "--memory",
    config.resources.memory,
  ];
  let capadd_params = [];
  let capdrop_params = [];
  if (config.resources.cap_add) {
    config.resources.cap_add.forEach(function (cap) {
      capadd_params.push("--cap-add");
      capadd_params.push(cap);
    });
  }
  if (config.resources.cap_drop) {
    config.resources.cap_drop.forEach(function (cap) {
      capdrop_params.push("--cap-drop");
      capdrop_params.push(cap);
    });
  }
  let shm_params = [];
  if (config.resources.shm) shm_params = ["--shm-size", config.resources.shm];
  let cpu_params = ["--cpu-shares", config.resources.cpu * DEFAULT_CPU_SHARE];
  let docker_base = ["docker", "run"]
    .concat(mounts)
    .concat(["--name", config.task_name + "_" + name, "--detach"])
    .concat(cpu_params)
    .concat(mem_params)
    .concat(shm_params)
    .concat(capadd_params)
    .concat(capdrop_params);
  let scraper_command = build_command_without(config, secret_fields);
  let args = docker_base
    .concat([image_human(config)])
    .concat([scraper_command]);
  return args.join(" ");
}

function trim_command(command, columns = 79) {
  // trim a string to espaced version (at most columns)

  let parts;
  if (typeof command == "object" && Object.isArray(command)) {
    parts = command.map(function (part) {
      return part.replace(/^--/, "");
    });
    command = parts.join(" ");
  } else {
    parts = command.split(" --");
  }
  // don't bother if command is not that long
  if (command.length <= columns) return command;

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
  lines[lines.length - 1] = last_line.substr(0, last_line.length - 1);

  let new_command = lines.join(sep);
  return new_command;
}

function short_id(id) {
  // short id of tasks (last chars)
  return id.substr(0, 5);
}

function formattedBytesSize(value) {
  if (!value) return "";
  return filesize(value, { base: 2, standard: "iec", precision: 3 }); // precision 3, display in KiB, MiB,... instead of KB, MB,...
}

function duplicate(dict) {
  return JSON.parse(JSON.stringify(dict));
}

function schedule_durations_dict(duration) {
  function single_duration(value, worker, on) {
    return { single: true, value: value, worker: worker, on: on };
  }

  function multiple_durations(min_value, max_value, workers) {
    let min_workers = Object.values(
      Object.filter(workers, function (item) {
        return item.value == min_value;
      })
    );
    let max_workers = Object.values(
      Object.filter(workers, function (item) {
        return item.value == max_value;
      })
    );
    return {
      single: false,
      min_value: min_value * 1000,
      max_value: max_value * 1000,
      min_workers: min_workers,
      max_workers: max_workers,
    };
  }

  if (!duration.available) {
    return single_duration(
      duration.default.value,
      "default",
      duration.default.on
    );
  }
  let min_worker = Object.min(duration.workers, "value");
  let max_worker = Object.max(duration.workers, "value");

  if (min_worker == max_worker) {
    return single_duration(
      duration.workers[min_worker].value,
      min_worker,
      duration.workers[min_worker].on
    );
  }
  let min_value = duration.workers[min_worker].value;
  let max_value = duration.workers[max_worker].value;
  return multiple_durations(min_value, max_value, duration.workers);
}

function secret_fields_for(offliner_flags_definition) {
  if (offliner_flags_definition === null) return [];
  return offliner_flags_definition
    .filter(function (item) {
      return "secret" in item && item.secret === true;
    })
    .map(function (item) {
      return item.data_key;
    });
}

function get_timezone_details() {
  let dt = DateTime.local();
  let diff = Duration.fromObject({ minutes: Math.abs(dt.o) });
  let offsetstr = "";
  let amount = "";
  if (diff.minutes % 60 == 0) {
    amount = `${diff.as("hour")} hour`;
    if (diff.minutes > 60) amount += "s";
  } else amount = `${diff.toHuman({ unitDisplay: "long" })}`;

  if (dt.o > 0) offsetstr = `${amount} ahead of UTC`;
  else if (dt.o < 0) offsetstr = `${amount} behind UTC`;
  else offsetstr = "in par with UTC";
  return { tz: dt.zoneName, offset: dt.o, offsetstr: offsetstr };
}

function getDelay(milliseconds) {
  // retrieve a promise making a pause in milliseconds
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

var DEFAULT_CPU_SHARE = 1024;

var ZIMFARM_WEBAPI =
  window.environ.ZIMFARM_WEBAPI || "https://api.farm.openzim.org/v1";
var cancelable_statuses = [
  "reserved",
  "started",
  "scraper_started",
  "scraper_completed",
  "scraper_killed",
];
var running_statuses = cancelable_statuses.concat(["cancel_requested"]);

export default {
  isProduction() {
    return ZIMFARM_WEBAPI.indexOf("https://") == 0;
  },
  zimfarm_webapi: ZIMFARM_WEBAPI,
  kiwix_download_url:
    window.environ.ZIMFARM_KIWIX_DOWNLOAD_URL ||
    "https://download.kiwix.org/zim",
  TASKS_LOAD_SCHEDULES_CHUNK_SIZE:
    parseInt(window.environ.ZIMFARM_TASKS_LOAD_SCHEDULES_CHUNK_SIZE, 10) || 5,
  TASKS_LOAD_SCHEDULES_DELAY:
    parseInt(window.environ.ZIMFARM_TASKS_LOAD_SCHEDULES_DELAY, 10) || 100,
  DEFAULT_CPU_SHARE: DEFAULT_CPU_SHARE, // used to generate docker cpu-shares
  DEFAULT_FIRE_PRIORITY: 5,
  DEFAULT_LIMIT: 20,
  LIMIT_CHOICES: [10, 20, 50, 100, 200],
  MAX_SCHEDULES_IN_SELECTION_REQUEST: 200,
  ALERT_DEFAULT_DURATION: 5,
  ALERT_LONG_DURATION: 10,
  ALERT_PERMANENT_DURATION: true,
  ROLES: [
    "editor",
    "editor-requester",
    "manager",
    "admin",
    "worker",
    "processor",
  ],
  TOKEN_COOKIE_EXPIRY: "180D", // 6 months
  COOKIE_LIFETIME_EXPIRY: "10Y", // 10 years
  TOKEN_COOKIE_NAME: "auth",
  cancelable_statuses: cancelable_statuses,
  running_statuses: running_statuses,
  contact_email: "contact@kiwix.org",
  categories: [
    "devdocs",
    "freecodecamp",
    "gutenberg",
    "ifixit",
    "other",
    "phet",
    "psiram",
    "stack_exchange",
    "ted",
    "openedx",
    "vikidia",
    "wikibooks",
    "wikihow",
    "wikinews",
    "wikipedia",
    "wikiquote",
    "wikisource",
    "wikispecies",
    "wikiversity",
    "wikivoyage",
    "wiktionary",
    "mindtouch",
  ], // list of categories for fileering
  warehouse_paths: [
    "/mindtouch",
    "/libretexts",
    "/devdocs",
    "/freecodecamp",
    "/gutenberg",
    "/ifixit",
    "/other",
    "/phet",
    "/psiram",
    "/stack_exchange",
    "/ted",
    "/mooc",
    "/videos",
    "/vikidia",
    "/wikibooks",
    "/wikihow",
    "/wikinews",
    "/wikipedia",
    "/wikiquote",
    "/wikisource",
    "/wikiversity",
    "/wikivoyage",
    "/wiktionary",
    "/zimit",
    "/.hidden/dev",
    "/.hidden/private",
    "/.hidden/endless",
    "/.hidden/bard",
    "/.hidden/bsf",
    "/.hidden/datacup",
    "/.hidden/custom_apps",
  ],
  periodicities: ["manually", "monthly", "quarterly", "biannualy", "annually"],
  memory_values: [
    536870912, // 512MiB
    1073741824, // 1GiB
    2147483648, // 2GiB
    3221225472, // 3GiB
    4294967296, // 4GiB
    5368709120, // 5GiB
    6442450944, // 6GiB
    7516192768, // 7GiB
    8589934592, // 8GiB
    9663676416, // 9GiB
    10737418240, // 10GiB
    11811160064, // 11GiB
    12884901888, // 12GiB
    13958643712, // 13GiB
    15032385536, // 14GiB
    16106127360, // 15GiB
    17179869184, // 16GiB
    18253611008, // 17GiB
    19327352832, // 18GiB
    20401094656, // 19GiB
    21474836480, // 20GiB
    22548578304, // 21GiB
    23622320128, // 22GiB
    24696061952, // 23GiB
    25769803776, // 24GiB
    26843545600, // 25GiB
    27917287424, // 26GiB
    28991029248, // 27GiB
    30064771072, // 28GiB
    31138512896, // 29GiB
    32212254720, // 30GiB
    33285996544, // 31GiB
    34359738368, // 32GiB
    51539607552, // 48GiB
    53687091200, // 50GB
    60129542144, // 56GB
    68719476736, // 64GiB
    77309411328, // 72GiB
    85899345920, // 80GiB
    94489280512, // 88GiB
    103079215104, // 96GiB
    107374182400, // 100GiB
    111669149696, // 104GiB
    120259084288, // 112GiB
    128849018880, // 120GiB
    137438953472, // 128GiB
  ],
  disk_values: [
    536870912, // 512MiB
    1073741824, // 1GiB
    2147483648, // 2GiB
    3221225472, // 3GiB
    4294967296, // 4GiB
    5368709120, // 5GiB
    10737418240, // 10GiB
    16106127360, // 15GiB
    21474836480, // 20GiB
    32212254720, // 30GiB
    42949672960, // 40GiB
    53687091200, // 50GiB
    80530636800, // 75GiB
    107374182400, // 100GiB
    134217728000, // 125GiB
    161061273600, // 150GiB
    187904819200, // 175GiB
    214748364800, // 200GiB
    241591910400, // 225GiB
    268435456000, // 250GiB
    295279001600, // 275GiB
    322122547200, // 300GiB
    375809638400, // 350GiB
    429496729600, // 400GiB
    483183820800, // 450GiB
    536870912000, // 500GiB
  ],
  yes_no(value, value_yes, value_no) {
    if (!value_yes) value_yes = "yes";
    if (!value_no) value_no = "no";
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

    if (response === undefined) {
      // no response
      //usually due to browser blocking failed OPTION preflight request
      return "Cross-Origin Request Blocked: preflight request failed.";
    }
    let status_text = response.statusText
      ? response.statusText
      : statuses[response.status];
    if (response.status == 400) {
      if (response.data && response.data.error)
        status_text += "<br />" + JSON.stringify(response.data.error);
      if (response.data && response.data.error_description)
        status_text +=
          "<br />" + JSON.stringify(response.data.error_description);
      if (response.data && response.data.message)
        status_text += "<br />" + JSON.stringify(response.data.message);
    }
    return response.status + ": " + status_text + ".";
  },
  format_dt: format_dt,
  format_duration: format_duration,
  format_duration_between: format_duration_between,
  params_serializer: params_serializer,
  now: now,
  image_human: image_human,
  image_url: image_url,
  logs_url: logs_url,
  artifacts_url: artifacts_url,
  build_docker_command: build_docker_command,
  build_command_without: build_command_without,
  trim_command: trim_command,
  from_now: from_now,
  short_id: short_id,
  formattedBytesSize: formattedBytesSize,
  duplicate: duplicate,
  schedule_durations_dict: schedule_durations_dict,
  secret_fields_for: secret_fields_for,
  tz_details: get_timezone_details(),
  fromSeconds: DateTime.fromSeconds,
  to_timestamp: to_timestamp,
  is_ios_firefox: isFirefoxOnIOS(),
  getDelay: getDelay,
};
