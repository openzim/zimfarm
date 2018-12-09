(window["webpackJsonp"] = window["webpackJsonp"] || []).push([["schedule-schedule-module"],{

/***/ "./node_modules/cronstrue/dist/cronstrue.js":
/*!**************************************************!*\
  !*** ./node_modules/cronstrue/dist/cronstrue.js ***!
  \**************************************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

(function webpackUniversalModuleDefinition(root, factory) {
	if(true)
		module.exports = factory();
	else {}
})(typeof self !== 'undefined' ? self : this, function() {
return /******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, {
/******/ 				configurable: false,
/******/ 				enumerable: true,
/******/ 				get: getter
/******/ 			});
/******/ 		}
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(__webpack_require__.s = 4);
/******/ })
/************************************************************************/
/******/ ([
/* 0 */
/***/ (function(module, exports, __webpack_require__) {

"use strict";

Object.defineProperty(exports, "__esModule", { value: true });
var stringUtilities_1 = __webpack_require__(1);
var cronParser_1 = __webpack_require__(2);
var ExpressionDescriptor = (function () {
    function ExpressionDescriptor(expression, options) {
        this.expression = expression;
        this.options = options;
        this.expressionParts = new Array(5);
        if (ExpressionDescriptor.locales[options.locale]) {
            this.i18n = ExpressionDescriptor.locales[options.locale];
        }
        else {
            console.warn("Locale '" + options.locale + "' could not be found; falling back to 'en'.");
            this.i18n = ExpressionDescriptor.locales["en"];
        }
        if (options.use24HourTimeFormat === undefined) {
            options.use24HourTimeFormat = this.i18n.use24HourTimeFormatByDefault();
        }
    }
    ExpressionDescriptor.toString = function (expression, _a) {
        var _b = _a === void 0 ? {} : _a, _c = _b.throwExceptionOnParseError, throwExceptionOnParseError = _c === void 0 ? true : _c, _d = _b.verbose, verbose = _d === void 0 ? false : _d, _e = _b.dayOfWeekStartIndexZero, dayOfWeekStartIndexZero = _e === void 0 ? true : _e, use24HourTimeFormat = _b.use24HourTimeFormat, _f = _b.locale, locale = _f === void 0 ? "en" : _f;
        var options = {
            throwExceptionOnParseError: throwExceptionOnParseError,
            verbose: verbose,
            dayOfWeekStartIndexZero: dayOfWeekStartIndexZero,
            use24HourTimeFormat: use24HourTimeFormat,
            locale: locale
        };
        var descripter = new ExpressionDescriptor(expression, options);
        return descripter.getFullDescription();
    };
    ExpressionDescriptor.initialize = function (localesLoader) {
        ExpressionDescriptor.specialCharacters = ["/", "-", ",", "*"];
        localesLoader.load(ExpressionDescriptor.locales);
    };
    ExpressionDescriptor.prototype.getFullDescription = function () {
        var description = "";
        try {
            var parser = new cronParser_1.CronParser(this.expression, this.options.dayOfWeekStartIndexZero);
            this.expressionParts = parser.parse();
            var timeSegment = this.getTimeOfDayDescription();
            var dayOfMonthDesc = this.getDayOfMonthDescription();
            var monthDesc = this.getMonthDescription();
            var dayOfWeekDesc = this.getDayOfWeekDescription();
            var yearDesc = this.getYearDescription();
            description += timeSegment + dayOfMonthDesc + dayOfWeekDesc + monthDesc + yearDesc;
            description = this.transformVerbosity(description, this.options.verbose);
            description = description.charAt(0).toLocaleUpperCase() + description.substr(1);
        }
        catch (ex) {
            if (!this.options.throwExceptionOnParseError) {
                description = this.i18n.anErrorOccuredWhenGeneratingTheExpressionD();
            }
            else {
                throw "" + ex;
            }
        }
        return description;
    };
    ExpressionDescriptor.prototype.getTimeOfDayDescription = function () {
        var secondsExpression = this.expressionParts[0];
        var minuteExpression = this.expressionParts[1];
        var hourExpression = this.expressionParts[2];
        var description = "";
        if (!stringUtilities_1.StringUtilities.containsAny(minuteExpression, ExpressionDescriptor.specialCharacters) &&
            !stringUtilities_1.StringUtilities.containsAny(hourExpression, ExpressionDescriptor.specialCharacters) &&
            !stringUtilities_1.StringUtilities.containsAny(secondsExpression, ExpressionDescriptor.specialCharacters)) {
            description += this.i18n.atSpace() + this.formatTime(hourExpression, minuteExpression, secondsExpression);
        }
        else if (!secondsExpression &&
            minuteExpression.indexOf("-") > -1 &&
            !(minuteExpression.indexOf(",") > -1) &&
            !stringUtilities_1.StringUtilities.containsAny(hourExpression, ExpressionDescriptor.specialCharacters)) {
            var minuteParts = minuteExpression.split("-");
            description += stringUtilities_1.StringUtilities.format(this.i18n.everyMinuteBetweenX0AndX1(), this.formatTime(hourExpression, minuteParts[0], ""), this.formatTime(hourExpression, minuteParts[1], ""));
        }
        else if (!secondsExpression &&
            hourExpression.indexOf(",") > -1 &&
            hourExpression.indexOf("-") == -1 &&
            hourExpression.indexOf("/") == -1 &&
            !stringUtilities_1.StringUtilities.containsAny(minuteExpression, ExpressionDescriptor.specialCharacters)) {
            var hourParts = hourExpression.split(",");
            description += this.i18n.at();
            for (var i = 0; i < hourParts.length; i++) {
                description += " ";
                description += this.formatTime(hourParts[i], minuteExpression, "");
                if (i < hourParts.length - 2) {
                    description += ",";
                }
                if (i == hourParts.length - 2) {
                    description += this.i18n.spaceAnd();
                }
            }
        }
        else {
            var secondsDescription = this.getSecondsDescription();
            var minutesDescription = this.getMinutesDescription();
            var hoursDescription = this.getHoursDescription();
            description += secondsDescription;
            if (description.length > 0) {
                description += ", ";
            }
            description += minutesDescription;
            if (description.length > 0) {
                description += ", ";
            }
            description += hoursDescription;
        }
        return description;
    };
    ExpressionDescriptor.prototype.getSecondsDescription = function () {
        var _this = this;
        var description = this.getSegmentDescription(this.expressionParts[0], this.i18n.everySecond(), function (s) {
            return s;
        }, function (s) {
            return stringUtilities_1.StringUtilities.format(_this.i18n.everyX0Seconds(), s);
        }, function (s) {
            return _this.i18n.secondsX0ThroughX1PastTheMinute();
        }, function (s) {
            return s == "0"
                ? ""
                : parseInt(s) < 20
                    ? _this.i18n.atX0SecondsPastTheMinute()
                    : _this.i18n.atX0SecondsPastTheMinuteGt20() || _this.i18n.atX0SecondsPastTheMinute();
        });
        return description;
    };
    ExpressionDescriptor.prototype.getMinutesDescription = function () {
        var _this = this;
        var description = this.getSegmentDescription(this.expressionParts[1], this.i18n.everyMinute(), function (s) {
            return s;
        }, function (s) {
            return stringUtilities_1.StringUtilities.format(_this.i18n.everyX0Minutes(), s);
        }, function (s) {
            return _this.i18n.minutesX0ThroughX1PastTheHour();
        }, function (s) {
            try {
                return s == "0"
                    ? ""
                    : parseInt(s) < 20
                        ? _this.i18n.atX0MinutesPastTheHour()
                        : _this.i18n.atX0MinutesPastTheHourGt20() || _this.i18n.atX0MinutesPastTheHour();
            }
            catch (e) {
                return _this.i18n.atX0MinutesPastTheHour();
            }
        });
        return description;
    };
    ExpressionDescriptor.prototype.getHoursDescription = function () {
        var _this = this;
        var expression = this.expressionParts[2];
        var description = this.getSegmentDescription(expression, this.i18n.everyHour(), function (s) {
            return _this.formatTime(s, "0", "");
        }, function (s) {
            return stringUtilities_1.StringUtilities.format(_this.i18n.everyX0Hours(), s);
        }, function (s) {
            return _this.i18n.betweenX0AndX1();
        }, function (s) {
            return _this.i18n.atX0();
        });
        return description;
    };
    ExpressionDescriptor.prototype.getDayOfWeekDescription = function () {
        var _this = this;
        var daysOfWeekNames = this.i18n.daysOfTheWeek();
        var description = null;
        if (this.expressionParts[5] == "*") {
            description = "";
        }
        else {
            description = this.getSegmentDescription(this.expressionParts[5], this.i18n.commaEveryDay(), function (s) {
                var exp = s;
                if (s.indexOf("#") > -1) {
                    exp = s.substr(0, s.indexOf("#"));
                }
                else if (s.indexOf("L") > -1) {
                    exp = exp.replace("L", "");
                }
                return daysOfWeekNames[parseInt(exp)];
            }, function (s) {
                return stringUtilities_1.StringUtilities.format(_this.i18n.commaEveryX0daysOfTheWeek(), s);
            }, function (s) {
                return _this.i18n.commaX0ThroughX1();
            }, function (s) {
                var format = null;
                if (s.indexOf("#") > -1) {
                    var dayOfWeekOfMonthNumber = s.substring(s.indexOf("#") + 1);
                    var dayOfWeekOfMonthDescription = null;
                    switch (dayOfWeekOfMonthNumber) {
                        case "1":
                            dayOfWeekOfMonthDescription = _this.i18n.first();
                            break;
                        case "2":
                            dayOfWeekOfMonthDescription = _this.i18n.second();
                            break;
                        case "3":
                            dayOfWeekOfMonthDescription = _this.i18n.third();
                            break;
                        case "4":
                            dayOfWeekOfMonthDescription = _this.i18n.fourth();
                            break;
                        case "5":
                            dayOfWeekOfMonthDescription = _this.i18n.fifth();
                            break;
                    }
                    format = _this.i18n.commaOnThe() + dayOfWeekOfMonthDescription + _this.i18n.spaceX0OfTheMonth();
                }
                else if (s.indexOf("L") > -1) {
                    format = _this.i18n.commaOnTheLastX0OfTheMonth();
                }
                else {
                    var domSpecified = _this.expressionParts[3] != "*";
                    format = domSpecified ? _this.i18n.commaAndOnX0() : _this.i18n.commaOnlyOnX0();
                }
                return format;
            });
        }
        return description;
    };
    ExpressionDescriptor.prototype.getMonthDescription = function () {
        var _this = this;
        var monthNames = this.i18n.monthsOfTheYear();
        var description = this.getSegmentDescription(this.expressionParts[4], "", function (s) {
            return monthNames[parseInt(s) - 1];
        }, function (s) {
            return stringUtilities_1.StringUtilities.format(_this.i18n.commaEveryX0Months(), s);
        }, function (s) {
            return _this.i18n.commaMonthX0ThroughMonthX1() || _this.i18n.commaX0ThroughX1();
        }, function (s) {
            return _this.i18n.commaOnlyInX0();
        });
        return description;
    };
    ExpressionDescriptor.prototype.getDayOfMonthDescription = function () {
        var _this = this;
        var description = null;
        var expression = this.expressionParts[3];
        switch (expression) {
            case "L":
                description = this.i18n.commaOnTheLastDayOfTheMonth();
                break;
            case "WL":
            case "LW":
                description = this.i18n.commaOnTheLastWeekdayOfTheMonth();
                break;
            default:
                var weekDayNumberMatches = expression.match(/(\d{1,2}W)|(W\d{1,2})/);
                if (weekDayNumberMatches) {
                    var dayNumber = parseInt(weekDayNumberMatches[0].replace("W", ""));
                    var dayString = dayNumber == 1
                        ? this.i18n.firstWeekday()
                        : stringUtilities_1.StringUtilities.format(this.i18n.weekdayNearestDayX0(), dayNumber.toString());
                    description = stringUtilities_1.StringUtilities.format(this.i18n.commaOnTheX0OfTheMonth(), dayString);
                    break;
                }
                else {
                    var lastDayOffSetMatches = expression.match(/L-(\d{1,2})/);
                    if (lastDayOffSetMatches) {
                        var offSetDays = lastDayOffSetMatches[1];
                        description = stringUtilities_1.StringUtilities.format(this.i18n.commaDaysBeforeTheLastDayOfTheMonth(), offSetDays);
                        break;
                    }
                    else {
                        description = this.getSegmentDescription(expression, this.i18n.commaEveryDay(), function (s) {
                            return s == "L" ? _this.i18n.lastDay() : s;
                        }, function (s) {
                            return s == "1" ? _this.i18n.commaEveryDay() : _this.i18n.commaEveryX0Days();
                        }, function (s) {
                            return _this.i18n.commaBetweenDayX0AndX1OfTheMonth();
                        }, function (s) {
                            return _this.i18n.commaOnDayX0OfTheMonth();
                        });
                    }
                    break;
                }
        }
        return description;
    };
    ExpressionDescriptor.prototype.getYearDescription = function () {
        var _this = this;
        var description = this.getSegmentDescription(this.expressionParts[6], "", function (s) {
            return /^\d+$/.test(s) ? new Date(parseInt(s), 1).getFullYear().toString() : s;
        }, function (s) {
            return stringUtilities_1.StringUtilities.format(_this.i18n.commaEveryX0Years(), s);
        }, function (s) {
            return _this.i18n.commaYearX0ThroughYearX1() || _this.i18n.commaX0ThroughX1();
        }, function (s) {
            return _this.i18n.commaOnlyInX0();
        });
        return description;
    };
    ExpressionDescriptor.prototype.getSegmentDescription = function (expression, allDescription, getSingleItemDescription, getIntervalDescriptionFormat, getBetweenDescriptionFormat, getDescriptionFormat) {
        var _this = this;
        var description = null;
        if (!expression) {
            description = "";
        }
        else if (expression === "*") {
            description = allDescription;
        }
        else if (!stringUtilities_1.StringUtilities.containsAny(expression, ["/", "-", ","])) {
            description = stringUtilities_1.StringUtilities.format(getDescriptionFormat(expression), getSingleItemDescription(expression));
        }
        else if (expression.indexOf("/") > -1) {
            var segments = expression.split("/");
            description = stringUtilities_1.StringUtilities.format(getIntervalDescriptionFormat(segments[1]), getSingleItemDescription(segments[1]));
            if (segments[0].indexOf("-") > -1) {
                var betweenSegmentDescription = this.generateBetweenSegmentDescription(segments[0], getBetweenDescriptionFormat, getSingleItemDescription);
                if (betweenSegmentDescription.indexOf(", ") != 0) {
                    description += ", ";
                }
                description += betweenSegmentDescription;
            }
            else if (!stringUtilities_1.StringUtilities.containsAny(segments[0], ["*", ","])) {
                var rangeItemDescription = stringUtilities_1.StringUtilities.format(getDescriptionFormat(segments[0]), getSingleItemDescription(segments[0]));
                rangeItemDescription = rangeItemDescription.replace(", ", "");
                description += stringUtilities_1.StringUtilities.format(this.i18n.commaStartingX0(), rangeItemDescription);
            }
        }
        else if (expression.indexOf(",") > -1) {
            var segments = expression.split(",");
            var descriptionContent = "";
            for (var i = 0; i < segments.length; i++) {
                if (i > 0 && segments.length > 2) {
                    descriptionContent += ",";
                    if (i < segments.length - 1) {
                        descriptionContent += " ";
                    }
                }
                if (i > 0 && segments.length > 1 && (i == segments.length - 1 || segments.length == 2)) {
                    descriptionContent += this.i18n.spaceAnd() + " ";
                }
                if (segments[i].indexOf("-") > -1) {
                    var betweenSegmentDescription = this.generateBetweenSegmentDescription(segments[i], function (s) {
                        return _this.i18n.commaX0ThroughX1();
                    }, getSingleItemDescription);
                    betweenSegmentDescription = betweenSegmentDescription.replace(", ", "");
                    descriptionContent += betweenSegmentDescription;
                }
                else {
                    descriptionContent += getSingleItemDescription(segments[i]);
                }
            }
            description = stringUtilities_1.StringUtilities.format(getDescriptionFormat(expression), descriptionContent);
        }
        else if (expression.indexOf("-") > -1) {
            description = this.generateBetweenSegmentDescription(expression, getBetweenDescriptionFormat, getSingleItemDescription);
        }
        return description;
    };
    ExpressionDescriptor.prototype.generateBetweenSegmentDescription = function (betweenExpression, getBetweenDescriptionFormat, getSingleItemDescription) {
        var description = "";
        var betweenSegments = betweenExpression.split("-");
        var betweenSegment1Description = getSingleItemDescription(betweenSegments[0]);
        var betweenSegment2Description = getSingleItemDescription(betweenSegments[1]);
        betweenSegment2Description = betweenSegment2Description.replace(":00", ":59");
        var betweenDescriptionFormat = getBetweenDescriptionFormat(betweenExpression);
        description += stringUtilities_1.StringUtilities.format(betweenDescriptionFormat, betweenSegment1Description, betweenSegment2Description);
        return description;
    };
    ExpressionDescriptor.prototype.formatTime = function (hourExpression, minuteExpression, secondExpression) {
        var hour = parseInt(hourExpression);
        var period = "";
        if (!this.options.use24HourTimeFormat) {
            period = hour >= 12 ? " PM" : " AM";
            if (hour > 12) {
                hour -= 12;
            }
            if (hour === 0) {
                hour = 12;
            }
        }
        var minute = minuteExpression;
        var second = "";
        if (secondExpression) {
            second = ":" + ("00" + secondExpression).substring(secondExpression.length);
        }
        return ("00" + hour.toString()).substring(hour.toString().length) + ":" + ("00" + minute.toString()).substring(minute.toString().length) + second + period;
    };
    ExpressionDescriptor.prototype.transformVerbosity = function (description, useVerboseFormat) {
        if (!useVerboseFormat) {
            description = description.replace(new RegExp(this.i18n.commaEveryMinute(), "g"), "");
            description = description.replace(new RegExp(this.i18n.commaEveryHour(), "g"), "");
            description = description.replace(new RegExp(this.i18n.commaEveryDay(), "g"), "");
        }
        return description;
    };
    ExpressionDescriptor.locales = {};
    return ExpressionDescriptor;
}());
exports.ExpressionDescriptor = ExpressionDescriptor;


/***/ }),
/* 1 */
/***/ (function(module, exports, __webpack_require__) {

"use strict";

Object.defineProperty(exports, "__esModule", { value: true });
var StringUtilities = (function () {
    function StringUtilities() {
    }
    StringUtilities.format = function (template) {
        var values = [];
        for (var _i = 1; _i < arguments.length; _i++) {
            values[_i - 1] = arguments[_i];
        }
        return template.replace(/%s/g, function () {
            return values.shift();
        });
    };
    StringUtilities.containsAny = function (text, searchStrings) {
        return searchStrings.some(function (c) {
            return text.indexOf(c) > -1;
        });
    };
    return StringUtilities;
}());
exports.StringUtilities = StringUtilities;


/***/ }),
/* 2 */
/***/ (function(module, exports, __webpack_require__) {

"use strict";

Object.defineProperty(exports, "__esModule", { value: true });
var CronParser = (function () {
    function CronParser(expression, dayOfWeekStartIndexZero) {
        if (dayOfWeekStartIndexZero === void 0) { dayOfWeekStartIndexZero = true; }
        this.expression = expression;
        this.dayOfWeekStartIndexZero = dayOfWeekStartIndexZero;
    }
    CronParser.prototype.parse = function () {
        var parsed = this.extractParts(this.expression);
        this.normalize(parsed);
        this.validate(parsed);
        return parsed;
    };
    CronParser.prototype.extractParts = function (expression) {
        if (!this.expression) {
            throw new Error("Expression is empty");
        }
        var parsed = expression.trim().split(" ");
        if (parsed.length < 5) {
            throw new Error("Expression has only " + parsed.length + " part" + (parsed.length == 1 ? "" : "s") + ". At least 5 parts are required.");
        }
        else if (parsed.length == 5) {
            parsed.unshift("");
            parsed.push("");
        }
        else if (parsed.length == 6) {
            if (/\d{4}$/.test(parsed[5])) {
                parsed.unshift("");
            }
            else {
                parsed.push("");
            }
        }
        else if (parsed.length > 7) {
            throw new Error("Expression has " + parsed.length + " parts; too many!");
        }
        return parsed;
    };
    CronParser.prototype.normalize = function (expressionParts) {
        var _this = this;
        expressionParts[3] = expressionParts[3].replace("?", "*");
        expressionParts[5] = expressionParts[5].replace("?", "*");
        if (expressionParts[0].indexOf("0/") == 0) {
            expressionParts[0] = expressionParts[0].replace("0/", "*/");
        }
        if (expressionParts[1].indexOf("0/") == 0) {
            expressionParts[1] = expressionParts[1].replace("0/", "*/");
        }
        if (expressionParts[2].indexOf("0/") == 0) {
            expressionParts[2] = expressionParts[2].replace("0/", "*/");
        }
        if (expressionParts[3].indexOf("1/") == 0) {
            expressionParts[3] = expressionParts[3].replace("1/", "*/");
        }
        if (expressionParts[4].indexOf("1/") == 0) {
            expressionParts[4] = expressionParts[4].replace("1/", "*/");
        }
        if (expressionParts[5].indexOf("1/") == 0) {
            expressionParts[5] = expressionParts[5].replace("1/", "*/");
        }
        if (expressionParts[6].indexOf("1/") == 0) {
            expressionParts[6] = expressionParts[6].replace("1/", "*/");
        }
        expressionParts[5] = expressionParts[5].replace(/(^\d)|([^#/\s]\d)/g, function (t) {
            var dowDigits = t.replace(/\D/, "");
            var dowDigitsAdjusted = dowDigits;
            if (_this.dayOfWeekStartIndexZero) {
                if (dowDigits == "7") {
                    dowDigitsAdjusted = "0";
                }
            }
            else {
                dowDigitsAdjusted = (parseInt(dowDigits) - 1).toString();
            }
            return t.replace(dowDigits, dowDigitsAdjusted);
        });
        if (expressionParts[5] == "L") {
            expressionParts[5] = "6";
        }
        if (expressionParts[3] == "?") {
            expressionParts[3] = "*";
        }
        if (expressionParts[3].indexOf("W") > -1 &&
            (expressionParts[3].indexOf(",") > -1 || expressionParts[3].indexOf("-") > -1)) {
            throw new Error("The 'W' character can be specified only when the day-of-month is a single day, not a range or list of days.");
        }
        var days = {
            SUN: 0,
            MON: 1,
            TUE: 2,
            WED: 3,
            THU: 4,
            FRI: 5,
            SAT: 6
        };
        for (var day in days) {
            expressionParts[5] = expressionParts[5].replace(new RegExp(day, "gi"), days[day].toString());
        }
        var months = {
            JAN: 1,
            FEB: 2,
            MAR: 3,
            APR: 4,
            MAY: 5,
            JUN: 6,
            JUL: 7,
            AUG: 8,
            SEP: 9,
            OCT: 10,
            NOV: 11,
            DEC: 12
        };
        for (var month in months) {
            expressionParts[4] = expressionParts[4].replace(new RegExp(month, "gi"), months[month].toString());
        }
        if (expressionParts[0] == "0") {
            expressionParts[0] = "";
        }
        for (var i = 0; i < expressionParts.length; i++) {
            if (expressionParts[i] == "*/1") {
                expressionParts[i] = "*";
            }
            if (expressionParts[i].indexOf("/") > -1 && !/^\*|\-|\,/.test(expressionParts[i])) {
                var stepRangeThrough = null;
                switch (i) {
                    case 4:
                        stepRangeThrough = "12";
                        break;
                    case 5:
                        stepRangeThrough = "6";
                        break;
                    case 6:
                        stepRangeThrough = "9999";
                        break;
                    default:
                        stepRangeThrough = null;
                        break;
                }
                if (stepRangeThrough != null) {
                    var parts = expressionParts[i].split("/");
                    expressionParts[i] = parts[0] + "-" + stepRangeThrough + "/" + parts[1];
                }
            }
        }
    };
    CronParser.prototype.validate = function (parsed) {
        this.assertNoInvalidCharacters("DOW", parsed[5]);
        this.assertNoInvalidCharacters("DOM", parsed[3]);
    };
    CronParser.prototype.assertNoInvalidCharacters = function (partDescription, expression) {
        var invalidChars = expression.match(/[A-KM-VX-Z]+/gi);
        if (invalidChars && invalidChars.length) {
            throw new Error(partDescription + " part contains invalid values: '" + invalidChars.toString() + "'");
        }
    };
    return CronParser;
}());
exports.CronParser = CronParser;


/***/ }),
/* 3 */
/***/ (function(module, exports, __webpack_require__) {

"use strict";

Object.defineProperty(exports, "__esModule", { value: true });
var en = (function () {
    function en() {
    }
    en.prototype.atX0SecondsPastTheMinuteGt20 = function () {
        return null;
    };
    en.prototype.atX0MinutesPastTheHourGt20 = function () {
        return null;
    };
    en.prototype.commaMonthX0ThroughMonthX1 = function () {
        return null;
    };
    en.prototype.commaYearX0ThroughYearX1 = function () {
        return null;
    };
    en.prototype.use24HourTimeFormatByDefault = function () {
        return false;
    };
    en.prototype.anErrorOccuredWhenGeneratingTheExpressionD = function () {
        return "An error occured when generating the expression description.  Check the cron expression syntax.";
    };
    en.prototype.everyMinute = function () {
        return "every minute";
    };
    en.prototype.everyHour = function () {
        return "every hour";
    };
    en.prototype.atSpace = function () {
        return "At ";
    };
    en.prototype.everyMinuteBetweenX0AndX1 = function () {
        return "Every minute between %s and %s";
    };
    en.prototype.at = function () {
        return "At";
    };
    en.prototype.spaceAnd = function () {
        return " and";
    };
    en.prototype.everySecond = function () {
        return "every second";
    };
    en.prototype.everyX0Seconds = function () {
        return "every %s seconds";
    };
    en.prototype.secondsX0ThroughX1PastTheMinute = function () {
        return "seconds %s through %s past the minute";
    };
    en.prototype.atX0SecondsPastTheMinute = function () {
        return "at %s seconds past the minute";
    };
    en.prototype.everyX0Minutes = function () {
        return "every %s minutes";
    };
    en.prototype.minutesX0ThroughX1PastTheHour = function () {
        return "minutes %s through %s past the hour";
    };
    en.prototype.atX0MinutesPastTheHour = function () {
        return "at %s minutes past the hour";
    };
    en.prototype.everyX0Hours = function () {
        return "every %s hours";
    };
    en.prototype.betweenX0AndX1 = function () {
        return "between %s and %s";
    };
    en.prototype.atX0 = function () {
        return "at %s";
    };
    en.prototype.commaEveryDay = function () {
        return ", every day";
    };
    en.prototype.commaEveryX0daysOfTheWeek = function () {
        return ", every %s days of the week";
    };
    en.prototype.commaX0ThroughX1 = function () {
        return ", %s through %s";
    };
    en.prototype.first = function () {
        return "first";
    };
    en.prototype.second = function () {
        return "second";
    };
    en.prototype.third = function () {
        return "third";
    };
    en.prototype.fourth = function () {
        return "fourth";
    };
    en.prototype.fifth = function () {
        return "fifth";
    };
    en.prototype.commaOnThe = function () {
        return ", on the ";
    };
    en.prototype.spaceX0OfTheMonth = function () {
        return " %s of the month";
    };
    en.prototype.lastDay = function () {
        return "the last day";
    };
    en.prototype.commaOnTheLastX0OfTheMonth = function () {
        return ", on the last %s of the month";
    };
    en.prototype.commaOnlyOnX0 = function () {
        return ", only on %s";
    };
    en.prototype.commaAndOnX0 = function () {
        return ", and on %s";
    };
    en.prototype.commaEveryX0Months = function () {
        return ", every %s months";
    };
    en.prototype.commaOnlyInX0 = function () {
        return ", only in %s";
    };
    en.prototype.commaOnTheLastDayOfTheMonth = function () {
        return ", on the last day of the month";
    };
    en.prototype.commaOnTheLastWeekdayOfTheMonth = function () {
        return ", on the last weekday of the month";
    };
    en.prototype.commaDaysBeforeTheLastDayOfTheMonth = function () {
        return ", %s days before the last day of the month";
    };
    en.prototype.firstWeekday = function () {
        return "first weekday";
    };
    en.prototype.weekdayNearestDayX0 = function () {
        return "weekday nearest day %s";
    };
    en.prototype.commaOnTheX0OfTheMonth = function () {
        return ", on the %s of the month";
    };
    en.prototype.commaEveryX0Days = function () {
        return ", every %s days";
    };
    en.prototype.commaBetweenDayX0AndX1OfTheMonth = function () {
        return ", between day %s and %s of the month";
    };
    en.prototype.commaOnDayX0OfTheMonth = function () {
        return ", on day %s of the month";
    };
    en.prototype.commaEveryMinute = function () {
        return ", every minute";
    };
    en.prototype.commaEveryHour = function () {
        return ", every hour";
    };
    en.prototype.commaEveryX0Years = function () {
        return ", every %s years";
    };
    en.prototype.commaStartingX0 = function () {
        return ", starting %s";
    };
    en.prototype.daysOfTheWeek = function () {
        return ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    };
    en.prototype.monthsOfTheYear = function () {
        return [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December"
        ];
    };
    return en;
}());
exports.en = en;


/***/ }),
/* 4 */
/***/ (function(module, exports, __webpack_require__) {

"use strict";

Object.defineProperty(exports, "__esModule", { value: true });
var expressionDescriptor_1 = __webpack_require__(0);
var enLocaleLoader_1 = __webpack_require__(5);
expressionDescriptor_1.ExpressionDescriptor.initialize(new enLocaleLoader_1.enLocaleLoader());
exports.default = expressionDescriptor_1.ExpressionDescriptor;
var toString = expressionDescriptor_1.ExpressionDescriptor.toString;
exports.toString = toString;


/***/ }),
/* 5 */
/***/ (function(module, exports, __webpack_require__) {

"use strict";

Object.defineProperty(exports, "__esModule", { value: true });
var en_1 = __webpack_require__(3);
var enLocaleLoader = (function () {
    function enLocaleLoader() {
    }
    enLocaleLoader.prototype.load = function (availableLocales) {
        availableLocales["en"] = new en_1.en();
    };
    return enLocaleLoader;
}());
exports.enLocaleLoader = enLocaleLoader;


/***/ })
/******/ ]);
});

/***/ }),

/***/ "./node_modules/time-ago-pipe/esm5/time-ago-pipe.js":
/*!**********************************************************!*\
  !*** ./node_modules/time-ago-pipe/esm5/time-ago-pipe.js ***!
  \**********************************************************/
/*! exports provided: TimeAgoPipe */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "TimeAgoPipe", function() { return TimeAgoPipe; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");

/**
 * @fileoverview added by tsickle
 * @suppress {checkTypes} checked by tsc
 */
var TimeAgoPipe = /** @class */ (function () {
    /**
     * @param {?} changeDetectorRef
     * @param {?} ngZone
     */
    function TimeAgoPipe(changeDetectorRef, ngZone) {
        this.changeDetectorRef = changeDetectorRef;
        this.ngZone = ngZone;
    }
    /**
     * @param {?} value
     * @return {?}
     */
    TimeAgoPipe.prototype.transform = function (value) {
        var _this = this;
        this.removeTimer();
        var /** @type {?} */ d = new Date(value);
        var /** @type {?} */ now = new Date();
        var /** @type {?} */ seconds = Math.round(Math.abs((now.getTime() - d.getTime()) / 1000));
        var /** @type {?} */ timeToUpdate = (Number.isNaN(seconds)) ? 1000 : this.getSecondsUntilUpdate(seconds) * 1000;
        this.timer = this.ngZone.runOutsideAngular(function () {
            if (typeof window !== 'undefined') {
                return window.setTimeout(function () {
                    _this.ngZone.run(function () { return _this.changeDetectorRef.markForCheck(); });
                }, timeToUpdate);
            }
            return null;
        });
        var /** @type {?} */ minutes = Math.round(Math.abs(seconds / 60));
        var /** @type {?} */ hours = Math.round(Math.abs(minutes / 60));
        var /** @type {?} */ days = Math.round(Math.abs(hours / 24));
        var /** @type {?} */ months = Math.round(Math.abs(days / 30.416));
        var /** @type {?} */ years = Math.round(Math.abs(days / 365));
        if (Number.isNaN(seconds)) {
            return '';
        }
        else if (seconds <= 45) {
            return 'a few seconds ago';
        }
        else if (seconds <= 90) {
            return 'a minute ago';
        }
        else if (minutes <= 45) {
            return minutes + ' minutes ago';
        }
        else if (minutes <= 90) {
            return 'an hour ago';
        }
        else if (hours <= 22) {
            return hours + ' hours ago';
        }
        else if (hours <= 36) {
            return 'a day ago';
        }
        else if (days <= 25) {
            return days + ' days ago';
        }
        else if (days <= 45) {
            return 'a month ago';
        }
        else if (days <= 345) {
            return months + ' months ago';
        }
        else if (days <= 545) {
            return 'a year ago';
        }
        else {
            // (days > 545)
            return years + ' years ago';
        }
    };
    /**
     * @return {?}
     */
    TimeAgoPipe.prototype.ngOnDestroy = function () {
        this.removeTimer();
    };
    /**
     * @return {?}
     */
    TimeAgoPipe.prototype.removeTimer = function () {
        if (this.timer) {
            window.clearTimeout(this.timer);
            this.timer = null;
        }
    };
    /**
     * @param {?} seconds
     * @return {?}
     */
    TimeAgoPipe.prototype.getSecondsUntilUpdate = function (seconds) {
        var /** @type {?} */ min = 60;
        var /** @type {?} */ hr = min * 60;
        var /** @type {?} */ day = hr * 24;
        if (seconds < min) {
            // less than 1 min, update every 2 secs
            return 2;
        }
        else if (seconds < hr) {
            // less than an hour, update every 30 secs
            return 30;
        }
        else if (seconds < day) {
            // less then a day, update every 5 mins
            return 300;
        }
        else {
            // update every hour
            return 3600;
        }
    };
    return TimeAgoPipe;
}());
TimeAgoPipe.decorators = [
    { type: _angular_core__WEBPACK_IMPORTED_MODULE_0__["Pipe"], args: [{
                name: 'timeAgo',
                pure: false
            },] },
];
/** @nocollapse */
TimeAgoPipe.ctorParameters = function () { return [
    { type: _angular_core__WEBPACK_IMPORTED_MODULE_0__["ChangeDetectorRef"], },
    { type: _angular_core__WEBPACK_IMPORTED_MODULE_0__["NgZone"], },
]; };
/**
 * @fileoverview added by tsickle
 * @suppress {checkTypes} checked by tsc
 */
/**
 * Generated bundle index. Do not edit.
 */

//# sourceMappingURL=time-ago-pipe.js.map


/***/ }),

/***/ "./src/app/schedule/schedule-beat/schedule-beat.component.css":
/*!********************************************************************!*\
  !*** ./src/app/schedule/schedule-beat/schedule-beat.component.css ***!
  \********************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "div.display {\n    margin: 2rem 0rem;\n    font-size: 2rem;\n    font-weight: 500;\n    text-align: center;\n}\n\nform {\n    display: flex;\n    flex-direction: column;\n    align-items: stretch;\n}\n\ntable {\n    border-collapse: collapse;\n    width:100%\n}\n\nth, td {\n    border: 1px solid #dddddd;\n    height: 2.5rem;\n}\n\ntr > td:first-child {\n    text-align: center;\n}\n\ntr > td:last-child > input {\n    border: 0;\n    box-sizing: border-box;\n    width: 100%;\n    height: 100%;\n    margin: 0;\n    padding-left: 0.5rem;\n    padding-right: 0.5rem;\n    font-size: 1rem;\n}\n\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvc2NoZWR1bGUvc2NoZWR1bGUtYmVhdC9zY2hlZHVsZS1iZWF0LmNvbXBvbmVudC5jc3MiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUE7SUFDSSxrQkFBa0I7SUFDbEIsZ0JBQWdCO0lBQ2hCLGlCQUFpQjtJQUNqQixtQkFBbUI7Q0FDdEI7O0FBRUQ7SUFDSSxjQUFjO0lBQ2QsdUJBQXVCO0lBQ3ZCLHFCQUFxQjtDQUN4Qjs7QUFFRDtJQUNJLDBCQUEwQjtJQUMxQixVQUFVO0NBQ2I7O0FBRUQ7SUFDSSwwQkFBMEI7SUFDMUIsZUFBZTtDQUNsQjs7QUFFRDtJQUNJLG1CQUFtQjtDQUN0Qjs7QUFFRDtJQUNJLFVBQVU7SUFDVix1QkFBdUI7SUFDdkIsWUFBWTtJQUNaLGFBQWE7SUFDYixVQUFVO0lBQ1YscUJBQXFCO0lBQ3JCLHNCQUFzQjtJQUN0QixnQkFBZ0I7Q0FDbkIiLCJmaWxlIjoic3JjL2FwcC9zY2hlZHVsZS9zY2hlZHVsZS1iZWF0L3NjaGVkdWxlLWJlYXQuY29tcG9uZW50LmNzcyIsInNvdXJjZXNDb250ZW50IjpbImRpdi5kaXNwbGF5IHtcbiAgICBtYXJnaW46IDJyZW0gMHJlbTtcbiAgICBmb250LXNpemU6IDJyZW07XG4gICAgZm9udC13ZWlnaHQ6IDUwMDtcbiAgICB0ZXh0LWFsaWduOiBjZW50ZXI7XG59XG5cbmZvcm0ge1xuICAgIGRpc3BsYXk6IGZsZXg7XG4gICAgZmxleC1kaXJlY3Rpb246IGNvbHVtbjtcbiAgICBhbGlnbi1pdGVtczogc3RyZXRjaDtcbn1cblxudGFibGUge1xuICAgIGJvcmRlci1jb2xsYXBzZTogY29sbGFwc2U7XG4gICAgd2lkdGg6MTAwJVxufVxuXG50aCwgdGQge1xuICAgIGJvcmRlcjogMXB4IHNvbGlkICNkZGRkZGQ7XG4gICAgaGVpZ2h0OiAyLjVyZW07XG59XG5cbnRyID4gdGQ6Zmlyc3QtY2hpbGQge1xuICAgIHRleHQtYWxpZ246IGNlbnRlcjtcbn1cblxudHIgPiB0ZDpsYXN0LWNoaWxkID4gaW5wdXQge1xuICAgIGJvcmRlcjogMDtcbiAgICBib3gtc2l6aW5nOiBib3JkZXItYm94O1xuICAgIHdpZHRoOiAxMDAlO1xuICAgIGhlaWdodDogMTAwJTtcbiAgICBtYXJnaW46IDA7XG4gICAgcGFkZGluZy1sZWZ0OiAwLjVyZW07XG4gICAgcGFkZGluZy1yaWdodDogMC41cmVtO1xuICAgIGZvbnQtc2l6ZTogMXJlbTtcbn1cblxuIl19 */"

/***/ }),

/***/ "./src/app/schedule/schedule-beat/schedule-beat.component.html":
/*!*********************************************************************!*\
  !*** ./src/app/schedule/schedule-beat/schedule-beat.component.html ***!
  \*********************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"title\">\n    Beat\n</div>\n<div class=\"display\">{{config.description}}</div>\n<form>\n    <div>\n        <table class=\"table-container\">\n            <thead>\n                <tr>\n                    <th>Parameter</th>\n                    <th>Value</th>\n                </tr>\n            </thead>\n            <tbody>\n                <tr>\n                    <td><label for=\"minute\">Minute</label></td>\n                    <td><input type=\"text\" id=\"minute\" name=\"minute\"\n                        [(ngModel)]=\"config.minute\" (ngModelChange)=\"configChanged()\"\n                        autocomplete=\"minute\" autocorrect=\"off\" autocapitalize=\"off\" spellcheck=\"false\">\n                    </td>\n                </tr>\n                <tr>\n                    <td><label for=\"hour\">Hour</label></td>\n                    <td><input type=\"text\" id=\"hour\" name=\"hour\"\n                        [(ngModel)]=\"config.hour\" (ngModelChange)=\"configChanged()\"\n                        autocomplete=\"off\" autocorrect=\"off\" autocapitalize=\"off\" spellcheck=\"false\">\n                    </td>\n                </tr>\n                <tr>\n                    <td><label for=\"day_of_week\">Day of Week</label></td>\n                    <td><input type=\"text\" id=\"day_of_week\" name=\"day_of_week\"\n                        [(ngModel)]=\"config.day_of_week\" (ngModelChange)=\"configChanged()\"\n                        autocomplete=\"off\" autocorrect=\"off\" autocapitalize=\"off\" spellcheck=\"false\">\n                    </td>\n                </tr>\n                <tr>\n                    <td><label for=\"day_of_month\">Day of Month</label></td>\n                    <td><input type=\"text\" id=\"day_of_month\" name=\"day_of_month\"\n                        [(ngModel)]=\"config.day_of_month\" (ngModelChange)=\"configChanged()\"\n                        autocomplete=\"off\" autocorrect=\"off\" autocapitalize=\"off\" spellcheck=\"false\">\n                    </td>\n                </tr>\n                <tr>\n                    <td><label for=\"month_of_year\">Month of Year</label></td>\n                    <td><input type=\"text\" id=\"month_of_year\" name=\"month_of_year\"\n                        [(ngModel)]=\"config.month_of_year\" (ngModelChange)=\"configChanged()\"\n                        autocomplete=\"off\" autocorrect=\"off\" autocapitalize=\"off\" spellcheck=\"false\">\n                    </td>\n                </tr>\n            </tbody>\n        </table>\n    </div>\n</form>"

/***/ }),

/***/ "./src/app/schedule/schedule-beat/schedule-beat.component.ts":
/*!*******************************************************************!*\
  !*** ./src/app/schedule/schedule-beat/schedule-beat.component.ts ***!
  \*******************************************************************/
/*! exports provided: ScheduleBeatComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ScheduleBeatComponent", function() { return ScheduleBeatComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_forms__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/forms */ "./node_modules/@angular/forms/fesm5/forms.js");
/* harmony import */ var _services_schedules_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../services/schedules.service */ "./src/app/services/schedules.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};



var ScheduleBeatComponent = /** @class */ (function () {
    function ScheduleBeatComponent() {
        this.name = new _angular_forms__WEBPACK_IMPORTED_MODULE_1__["FormControl"]('');
        this.config = new _services_schedules_service__WEBPACK_IMPORTED_MODULE_2__["CrontabBeatConfig"]({});
    }
    ScheduleBeatComponent.prototype.ngOnInit = function () {
    };
    ScheduleBeatComponent.prototype.configChanged = function () {
        this.config.updateDescription();
        console.log(this.config);
    };
    ScheduleBeatComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-schedule-beat',
            template: __webpack_require__(/*! ./schedule-beat.component.html */ "./src/app/schedule/schedule-beat/schedule-beat.component.html"),
            styles: [__webpack_require__(/*! ./schedule-beat.component.css */ "./src/app/schedule/schedule-beat/schedule-beat.component.css"), __webpack_require__(/*! ../schedule.shared.css */ "./src/app/schedule/schedule.shared.css")]
        }),
        __metadata("design:paramtypes", [])
    ], ScheduleBeatComponent);
    return ScheduleBeatComponent;
}());



/***/ }),

/***/ "./src/app/schedule/schedule-detail/schedule-detail.component.css":
/*!************************************************************************!*\
  !*** ./src/app/schedule/schedule-detail/schedule-detail.component.css ***!
  \************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".container {\n    display: flex;\n    flex-direction: row;\n    align-items: flex-start;\n    max-width: 55rem;\n    margin-left: auto;\n    margin-right: auto;\n}\n\n.content {\n    margin: 1rem 0.5rem;\n}\n\n.content:first-child {\n    margin-left: 1rem;\n}\n\n.content:last-child {\n    margin-right: 1rem;\n    flex: 1;\n}\n\n@media only screen and (max-width: 600px) {\n    .container {\n        flex-direction: column;\n        align-items: stretch;\n    }\n\n    .content {\n        margin: 0.5rem 1rem;\n    }\n    \n    .content:first-child {\n        margin-top: 1rem;\n    }\n    \n    .content:last-child {\n        margin-bottom: 1rem;\n    }\n}\n\n.nav-menu {\n    width: 14rem;\n    border: 1px #e1e4e8 solid;\n    border-radius: 4px;\n}\n\n@media only screen and (max-width: 600px) {\n    .nav-menu {\n        width: unset;\n    }\n}\n\n.nav-menu > .item {\n    border-bottom: 1px #e1e4e8 solid;\n    display: flex;\n    flex-direction: row;\n    font-size: 0.9rem;\n}\n\n.nav-menu > .item:first-child {\n    border-top-left-radius: 4px;\n    border-top-right-radius: 4px;\n}\n\n.nav-menu > .item:last-child {\n    border-bottom: none;\n}\n\n.nav-menu > .title {\n    font-size: 1rem;\n    font-weight: 500;\n    padding: 0.75rem;\n    background-color: #F3F5F8;\n}\n\n.nav-menu > .item > a {\n    flex: 1;\n    color: black;\n    text-decoration: none;\n    display: flex;\n    align-items: stretch;\n}\n\n.nav-menu > .item > a:hover {\n    background-color: #F6F8FA;\n}\n\n.nav-menu > .item > a > div.indicator {\n    width: 2px;\n}\n\n.nav-menu > .item > a.active > div.indicator {\n    background-color: #dc3545;\n}\n\n.nav-menu > .item:last-child > a.active > div.indicator {\n    border-bottom-left-radius: 2px;\n}\n\n.nav-menu > .item > a > span {\n    margin: 0.75rem;\n}\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvc2NoZWR1bGUvc2NoZWR1bGUtZGV0YWlsL3NjaGVkdWxlLWRldGFpbC5jb21wb25lbnQuY3NzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUFBO0lBQ0ksY0FBYztJQUNkLG9CQUFvQjtJQUNwQix3QkFBd0I7SUFDeEIsaUJBQWlCO0lBQ2pCLGtCQUFrQjtJQUNsQixtQkFBbUI7Q0FDdEI7O0FBRUQ7SUFDSSxvQkFBb0I7Q0FDdkI7O0FBRUQ7SUFDSSxrQkFBa0I7Q0FDckI7O0FBRUQ7SUFDSSxtQkFBbUI7SUFDbkIsUUFBUTtDQUNYOztBQUVEO0lBQ0k7UUFDSSx1QkFBdUI7UUFDdkIscUJBQXFCO0tBQ3hCOztJQUVEO1FBQ0ksb0JBQW9CO0tBQ3ZCOztJQUVEO1FBQ0ksaUJBQWlCO0tBQ3BCOztJQUVEO1FBQ0ksb0JBQW9CO0tBQ3ZCO0NBQ0o7O0FBRUQ7SUFDSSxhQUFhO0lBQ2IsMEJBQTBCO0lBQzFCLG1CQUFtQjtDQUN0Qjs7QUFFRDtJQUNJO1FBQ0ksYUFBYTtLQUNoQjtDQUNKOztBQUVEO0lBQ0ksaUNBQWlDO0lBQ2pDLGNBQWM7SUFDZCxvQkFBb0I7SUFDcEIsa0JBQWtCO0NBQ3JCOztBQUVEO0lBQ0ksNEJBQTRCO0lBQzVCLDZCQUE2QjtDQUNoQzs7QUFFRDtJQUNJLG9CQUFvQjtDQUN2Qjs7QUFFRDtJQUNJLGdCQUFnQjtJQUNoQixpQkFBaUI7SUFDakIsaUJBQWlCO0lBQ2pCLDBCQUEwQjtDQUM3Qjs7QUFFRDtJQUNJLFFBQVE7SUFDUixhQUFhO0lBQ2Isc0JBQXNCO0lBQ3RCLGNBQWM7SUFDZCxxQkFBcUI7Q0FDeEI7O0FBRUQ7SUFDSSwwQkFBMEI7Q0FDN0I7O0FBRUQ7SUFDSSxXQUFXO0NBQ2Q7O0FBRUQ7SUFDSSwwQkFBMEI7Q0FDN0I7O0FBRUQ7SUFDSSwrQkFBK0I7Q0FDbEM7O0FBRUQ7SUFDSSxnQkFBZ0I7Q0FDbkIiLCJmaWxlIjoic3JjL2FwcC9zY2hlZHVsZS9zY2hlZHVsZS1kZXRhaWwvc2NoZWR1bGUtZGV0YWlsLmNvbXBvbmVudC5jc3MiLCJzb3VyY2VzQ29udGVudCI6WyIuY29udGFpbmVyIHtcbiAgICBkaXNwbGF5OiBmbGV4O1xuICAgIGZsZXgtZGlyZWN0aW9uOiByb3c7XG4gICAgYWxpZ24taXRlbXM6IGZsZXgtc3RhcnQ7XG4gICAgbWF4LXdpZHRoOiA1NXJlbTtcbiAgICBtYXJnaW4tbGVmdDogYXV0bztcbiAgICBtYXJnaW4tcmlnaHQ6IGF1dG87XG59XG5cbi5jb250ZW50IHtcbiAgICBtYXJnaW46IDFyZW0gMC41cmVtO1xufVxuXG4uY29udGVudDpmaXJzdC1jaGlsZCB7XG4gICAgbWFyZ2luLWxlZnQ6IDFyZW07XG59XG5cbi5jb250ZW50Omxhc3QtY2hpbGQge1xuICAgIG1hcmdpbi1yaWdodDogMXJlbTtcbiAgICBmbGV4OiAxO1xufVxuXG5AbWVkaWEgb25seSBzY3JlZW4gYW5kIChtYXgtd2lkdGg6IDYwMHB4KSB7XG4gICAgLmNvbnRhaW5lciB7XG4gICAgICAgIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XG4gICAgICAgIGFsaWduLWl0ZW1zOiBzdHJldGNoO1xuICAgIH1cblxuICAgIC5jb250ZW50IHtcbiAgICAgICAgbWFyZ2luOiAwLjVyZW0gMXJlbTtcbiAgICB9XG4gICAgXG4gICAgLmNvbnRlbnQ6Zmlyc3QtY2hpbGQge1xuICAgICAgICBtYXJnaW4tdG9wOiAxcmVtO1xuICAgIH1cbiAgICBcbiAgICAuY29udGVudDpsYXN0LWNoaWxkIHtcbiAgICAgICAgbWFyZ2luLWJvdHRvbTogMXJlbTtcbiAgICB9XG59XG5cbi5uYXYtbWVudSB7XG4gICAgd2lkdGg6IDE0cmVtO1xuICAgIGJvcmRlcjogMXB4ICNlMWU0ZTggc29saWQ7XG4gICAgYm9yZGVyLXJhZGl1czogNHB4O1xufVxuXG5AbWVkaWEgb25seSBzY3JlZW4gYW5kIChtYXgtd2lkdGg6IDYwMHB4KSB7XG4gICAgLm5hdi1tZW51IHtcbiAgICAgICAgd2lkdGg6IHVuc2V0O1xuICAgIH1cbn1cblxuLm5hdi1tZW51ID4gLml0ZW0ge1xuICAgIGJvcmRlci1ib3R0b206IDFweCAjZTFlNGU4IHNvbGlkO1xuICAgIGRpc3BsYXk6IGZsZXg7XG4gICAgZmxleC1kaXJlY3Rpb246IHJvdztcbiAgICBmb250LXNpemU6IDAuOXJlbTtcbn1cblxuLm5hdi1tZW51ID4gLml0ZW06Zmlyc3QtY2hpbGQge1xuICAgIGJvcmRlci10b3AtbGVmdC1yYWRpdXM6IDRweDtcbiAgICBib3JkZXItdG9wLXJpZ2h0LXJhZGl1czogNHB4O1xufVxuXG4ubmF2LW1lbnUgPiAuaXRlbTpsYXN0LWNoaWxkIHtcbiAgICBib3JkZXItYm90dG9tOiBub25lO1xufVxuXG4ubmF2LW1lbnUgPiAudGl0bGUge1xuICAgIGZvbnQtc2l6ZTogMXJlbTtcbiAgICBmb250LXdlaWdodDogNTAwO1xuICAgIHBhZGRpbmc6IDAuNzVyZW07XG4gICAgYmFja2dyb3VuZC1jb2xvcjogI0YzRjVGODtcbn1cblxuLm5hdi1tZW51ID4gLml0ZW0gPiBhIHtcbiAgICBmbGV4OiAxO1xuICAgIGNvbG9yOiBibGFjaztcbiAgICB0ZXh0LWRlY29yYXRpb246IG5vbmU7XG4gICAgZGlzcGxheTogZmxleDtcbiAgICBhbGlnbi1pdGVtczogc3RyZXRjaDtcbn1cblxuLm5hdi1tZW51ID4gLml0ZW0gPiBhOmhvdmVyIHtcbiAgICBiYWNrZ3JvdW5kLWNvbG9yOiAjRjZGOEZBO1xufVxuXG4ubmF2LW1lbnUgPiAuaXRlbSA+IGEgPiBkaXYuaW5kaWNhdG9yIHtcbiAgICB3aWR0aDogMnB4O1xufVxuXG4ubmF2LW1lbnUgPiAuaXRlbSA+IGEuYWN0aXZlID4gZGl2LmluZGljYXRvciB7XG4gICAgYmFja2dyb3VuZC1jb2xvcjogI2RjMzU0NTtcbn1cblxuLm5hdi1tZW51ID4gLml0ZW06bGFzdC1jaGlsZCA+IGEuYWN0aXZlID4gZGl2LmluZGljYXRvciB7XG4gICAgYm9yZGVyLWJvdHRvbS1sZWZ0LXJhZGl1czogMnB4O1xufVxuXG4ubmF2LW1lbnUgPiAuaXRlbSA+IGEgPiBzcGFuIHtcbiAgICBtYXJnaW46IDAuNzVyZW07XG59XG4iXX0= */"

/***/ }),

/***/ "./src/app/schedule/schedule-detail/schedule-detail.component.html":
/*!*************************************************************************!*\
  !*** ./src/app/schedule/schedule-detail/schedule-detail.component.html ***!
  \*************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"container\">\n    <div class=\"content nav-menu\">\n        <div class=\"item title\">{{name}}</div>\n        <div class=\"item\">\n            <a routerLink=\"./\" routerLinkActive=\"active\" [routerLinkActiveOptions]=\"{exact: true}\">\n                <div class=\"indicator\"></div>\n                <span>Overview</span>\n            </a>\n        </div>\n        <div class=\"item\">\n            <a routerLink=\"beat\" routerLinkActive=\"active\">\n                <div class=\"indicator\"></div>\n                <span>Beat</span>\n            </a>\n        </div>\n        <div class=\"item\">\n            <a routerLink=\"offliner\" routerLinkActive=\"active\">\n                <div class=\"indicator\"></div>\n                <span>Offliner</span>\n            </a>\n        </div>\n        <div class=\"item\">\n            <a routerLink=\"task\" routerLinkActive=\"active\">\n                <div class=\"indicator\"></div>\n                <span>Task</span>\n            </a>\n        </div>\n    </div>\n    <div class=\"content\">\n        <router-outlet></router-outlet>\n    </div>\n</div>"

/***/ }),

/***/ "./src/app/schedule/schedule-detail/schedule-detail.component.ts":
/*!***********************************************************************!*\
  !*** ./src/app/schedule/schedule-detail/schedule-detail.component.ts ***!
  \***********************************************************************/
/*! exports provided: ScheduleDetailComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ScheduleDetailComponent", function() { return ScheduleDetailComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};


var ScheduleDetailComponent = /** @class */ (function () {
    function ScheduleDetailComponent(route) {
        this.route = route;
    }
    ScheduleDetailComponent.prototype.ngOnInit = function () {
        this.name = this.route.snapshot.paramMap.get('name');
    };
    ScheduleDetailComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            template: __webpack_require__(/*! ./schedule-detail.component.html */ "./src/app/schedule/schedule-detail/schedule-detail.component.html"),
            styles: [__webpack_require__(/*! ./schedule-detail.component.css */ "./src/app/schedule/schedule-detail/schedule-detail.component.css")]
        }),
        __metadata("design:paramtypes", [_angular_router__WEBPACK_IMPORTED_MODULE_1__["ActivatedRoute"]])
    ], ScheduleDetailComponent);
    return ScheduleDetailComponent;
}());



/***/ }),

/***/ "./src/app/schedule/schedule-list/schedule-list.component.css":
/*!********************************************************************!*\
  !*** ./src/app/schedule/schedule-list/schedule-list.component.css ***!
  \********************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".container {\n    display: flex;\n    flex-direction: column;\n}\n\n.content {\n    margin-left: 1rem;\n    margin-right: 1rem;\n    margin-top: 0.25rem;\n    margin-bottom: 0.25rem;\n}\n\n.content:first-child {\n    margin-top: 0.5rem;\n}\n\n.content:last-child {\n    margin-bottom: 0.5rem;\n}\n\n@media only screen and (max-width: 768px) {\n    .content {\n        margin-left: 0;\n        margin-right: 0;\n    }\n}\n\n.toolbar {\n    padding: 0 0.25rem;\n    display: flex;\n    justify-content: space-between;\n}\n\n.pagination {\n    display: flex;\n    list-style: none;\n    padding: 0;\n    margin: 0.25rem;\n    border: 1px solid #dddddd;\n    border-radius: 4px;\n    background-color: #f8f8f8;\n    overflow: hidden;\n}\n\n.page-item {\n    border-right: 1px solid #dddddd;\n    display: list-item;\n}\n\n.page-item:hover {\n    background-color: #eeeeee;\n}\n\n.page-item:active {\n    background-color: #e9ecef;\n}\n\n.page-item:last-child {\n    border-right: 0px;\n}\n\n.page-item > button {\n    box-sizing: border-box;\n    background-color: transparent;\n    border: none;\n    cursor: pointer;\n    font-size: 1rem;\n    font-weight: 500;\n    padding: 0.25rem 0.5rem;\n    color: #007bff;\n}\n\n.table-container {\n    overflow-x: auto;\n}\n\ntable {\n    border-collapse: collapse;\n    width: 100%;\n}\n\nthead > tr {\n    border-top: 2px solid #dddddd;\n    border-bottom: 2px solid #dddddd;\n}\n\ntbody > tr {\n    border-bottom: 1px solid #dddddd;\n}\n\ntbody > tr:hover {\n    background-color: #f8f8f8;\n}\n\ntd, th {\n    text-align: center;\n    padding: 1rem;\n}\n\ntd.name  .circle {\n    width: 0.5rem;\n    height: 0.5rem;\n    border-radius: 0.15rem;\n    border-width: 1px;\n    border-style: solid;\n    margin-right: 0.5rem;\n    background: #bbbbbb;\n    border-color: #999999;\n    float: left;\n}\n\ntd.name .enabled {\n    background: #28a745;\n    border-color: #1e7b34;\n}\n\ntd.name a {\n    color: #1B6CD0;\n    font-weight: 500;\n    text-decoration: none;\n}\n\ntd.name a:hover {\n    text-decoration: underline;\n}\n\ntd.run_every {\n    text-align: left;\n    min-width: 10rem;\n}\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvc2NoZWR1bGUvc2NoZWR1bGUtbGlzdC9zY2hlZHVsZS1saXN0LmNvbXBvbmVudC5jc3MiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUE7SUFDSSxjQUFjO0lBQ2QsdUJBQXVCO0NBQzFCOztBQUVEO0lBQ0ksa0JBQWtCO0lBQ2xCLG1CQUFtQjtJQUNuQixvQkFBb0I7SUFDcEIsdUJBQXVCO0NBQzFCOztBQUVEO0lBQ0ksbUJBQW1CO0NBQ3RCOztBQUVEO0lBQ0ksc0JBQXNCO0NBQ3pCOztBQUVEO0lBQ0k7UUFDSSxlQUFlO1FBQ2YsZ0JBQWdCO0tBQ25CO0NBQ0o7O0FBRUQ7SUFDSSxtQkFBbUI7SUFDbkIsY0FBYztJQUNkLCtCQUErQjtDQUNsQzs7QUFFRDtJQUNJLGNBQWM7SUFDZCxpQkFBaUI7SUFDakIsV0FBVztJQUNYLGdCQUFnQjtJQUNoQiwwQkFBMEI7SUFDMUIsbUJBQW1CO0lBQ25CLDBCQUEwQjtJQUMxQixpQkFBaUI7Q0FDcEI7O0FBRUQ7SUFDSSxnQ0FBZ0M7SUFDaEMsbUJBQW1CO0NBQ3RCOztBQUVEO0lBQ0ksMEJBQTBCO0NBQzdCOztBQUVEO0lBQ0ksMEJBQTBCO0NBQzdCOztBQUVEO0lBQ0ksa0JBQWtCO0NBQ3JCOztBQUVEO0lBQ0ksdUJBQXVCO0lBQ3ZCLDhCQUE4QjtJQUM5QixhQUFhO0lBQ2IsZ0JBQWdCO0lBQ2hCLGdCQUFnQjtJQUNoQixpQkFBaUI7SUFDakIsd0JBQXdCO0lBQ3hCLGVBQWU7Q0FDbEI7O0FBRUQ7SUFDSSxpQkFBaUI7Q0FDcEI7O0FBRUQ7SUFDSSwwQkFBMEI7SUFDMUIsWUFBWTtDQUNmOztBQUVEO0lBQ0ksOEJBQThCO0lBQzlCLGlDQUFpQztDQUNwQzs7QUFFRDtJQUNJLGlDQUFpQztDQUNwQzs7QUFFRDtJQUNJLDBCQUEwQjtDQUM3Qjs7QUFFRDtJQUNJLG1CQUFtQjtJQUNuQixjQUFjO0NBQ2pCOztBQUVEO0lBQ0ksY0FBYztJQUNkLGVBQWU7SUFHZix1QkFBdUI7SUFDdkIsa0JBQWtCO0lBQ2xCLG9CQUFvQjtJQUNwQixxQkFBcUI7SUFDckIsb0JBQW9CO0lBQ3BCLHNCQUFzQjtJQUN0QixZQUFZO0NBQ2Y7O0FBRUQ7SUFDSSxvQkFBb0I7SUFDcEIsc0JBQXNCO0NBQ3pCOztBQUVEO0lBQ0ksZUFBZTtJQUNmLGlCQUFpQjtJQUNqQixzQkFBc0I7Q0FDekI7O0FBRUQ7SUFDSSwyQkFBMkI7Q0FDOUI7O0FBRUQ7SUFDSSxpQkFBaUI7SUFDakIsaUJBQWlCO0NBQ3BCIiwiZmlsZSI6InNyYy9hcHAvc2NoZWR1bGUvc2NoZWR1bGUtbGlzdC9zY2hlZHVsZS1saXN0LmNvbXBvbmVudC5jc3MiLCJzb3VyY2VzQ29udGVudCI6WyIuY29udGFpbmVyIHtcbiAgICBkaXNwbGF5OiBmbGV4O1xuICAgIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XG59XG5cbi5jb250ZW50IHtcbiAgICBtYXJnaW4tbGVmdDogMXJlbTtcbiAgICBtYXJnaW4tcmlnaHQ6IDFyZW07XG4gICAgbWFyZ2luLXRvcDogMC4yNXJlbTtcbiAgICBtYXJnaW4tYm90dG9tOiAwLjI1cmVtO1xufVxuXG4uY29udGVudDpmaXJzdC1jaGlsZCB7XG4gICAgbWFyZ2luLXRvcDogMC41cmVtO1xufVxuXG4uY29udGVudDpsYXN0LWNoaWxkIHtcbiAgICBtYXJnaW4tYm90dG9tOiAwLjVyZW07XG59XG5cbkBtZWRpYSBvbmx5IHNjcmVlbiBhbmQgKG1heC13aWR0aDogNzY4cHgpIHtcbiAgICAuY29udGVudCB7XG4gICAgICAgIG1hcmdpbi1sZWZ0OiAwO1xuICAgICAgICBtYXJnaW4tcmlnaHQ6IDA7XG4gICAgfVxufVxuXG4udG9vbGJhciB7XG4gICAgcGFkZGluZzogMCAwLjI1cmVtO1xuICAgIGRpc3BsYXk6IGZsZXg7XG4gICAganVzdGlmeS1jb250ZW50OiBzcGFjZS1iZXR3ZWVuO1xufVxuXG4ucGFnaW5hdGlvbiB7XG4gICAgZGlzcGxheTogZmxleDtcbiAgICBsaXN0LXN0eWxlOiBub25lO1xuICAgIHBhZGRpbmc6IDA7XG4gICAgbWFyZ2luOiAwLjI1cmVtO1xuICAgIGJvcmRlcjogMXB4IHNvbGlkICNkZGRkZGQ7XG4gICAgYm9yZGVyLXJhZGl1czogNHB4O1xuICAgIGJhY2tncm91bmQtY29sb3I6ICNmOGY4Zjg7XG4gICAgb3ZlcmZsb3c6IGhpZGRlbjtcbn1cblxuLnBhZ2UtaXRlbSB7XG4gICAgYm9yZGVyLXJpZ2h0OiAxcHggc29saWQgI2RkZGRkZDtcbiAgICBkaXNwbGF5OiBsaXN0LWl0ZW07XG59XG5cbi5wYWdlLWl0ZW06aG92ZXIge1xuICAgIGJhY2tncm91bmQtY29sb3I6ICNlZWVlZWU7XG59XG5cbi5wYWdlLWl0ZW06YWN0aXZlIHtcbiAgICBiYWNrZ3JvdW5kLWNvbG9yOiAjZTllY2VmO1xufVxuXG4ucGFnZS1pdGVtOmxhc3QtY2hpbGQge1xuICAgIGJvcmRlci1yaWdodDogMHB4O1xufVxuXG4ucGFnZS1pdGVtID4gYnV0dG9uIHtcbiAgICBib3gtc2l6aW5nOiBib3JkZXItYm94O1xuICAgIGJhY2tncm91bmQtY29sb3I6IHRyYW5zcGFyZW50O1xuICAgIGJvcmRlcjogbm9uZTtcbiAgICBjdXJzb3I6IHBvaW50ZXI7XG4gICAgZm9udC1zaXplOiAxcmVtO1xuICAgIGZvbnQtd2VpZ2h0OiA1MDA7XG4gICAgcGFkZGluZzogMC4yNXJlbSAwLjVyZW07XG4gICAgY29sb3I6ICMwMDdiZmY7XG59XG5cbi50YWJsZS1jb250YWluZXIge1xuICAgIG92ZXJmbG93LXg6IGF1dG87XG59XG5cbnRhYmxlIHtcbiAgICBib3JkZXItY29sbGFwc2U6IGNvbGxhcHNlO1xuICAgIHdpZHRoOiAxMDAlO1xufVxuXG50aGVhZCA+IHRyIHtcbiAgICBib3JkZXItdG9wOiAycHggc29saWQgI2RkZGRkZDtcbiAgICBib3JkZXItYm90dG9tOiAycHggc29saWQgI2RkZGRkZDtcbn1cblxudGJvZHkgPiB0ciB7XG4gICAgYm9yZGVyLWJvdHRvbTogMXB4IHNvbGlkICNkZGRkZGQ7XG59XG5cbnRib2R5ID4gdHI6aG92ZXIge1xuICAgIGJhY2tncm91bmQtY29sb3I6ICNmOGY4Zjg7XG59XG5cbnRkLCB0aCB7XG4gICAgdGV4dC1hbGlnbjogY2VudGVyO1xuICAgIHBhZGRpbmc6IDFyZW07XG59XG5cbnRkLm5hbWUgIC5jaXJjbGUge1xuICAgIHdpZHRoOiAwLjVyZW07XG4gICAgaGVpZ2h0OiAwLjVyZW07XG4gICAgLXdlYmtpdC1ib3JkZXItcmFkaXVzOiAwLjE1cmVtO1xuICAgIC1tb3otYm9yZGVyLXJhZGl1czogMC4xNXJlbTtcbiAgICBib3JkZXItcmFkaXVzOiAwLjE1cmVtO1xuICAgIGJvcmRlci13aWR0aDogMXB4O1xuICAgIGJvcmRlci1zdHlsZTogc29saWQ7XG4gICAgbWFyZ2luLXJpZ2h0OiAwLjVyZW07XG4gICAgYmFja2dyb3VuZDogI2JiYmJiYjtcbiAgICBib3JkZXItY29sb3I6ICM5OTk5OTk7XG4gICAgZmxvYXQ6IGxlZnQ7XG59XG5cbnRkLm5hbWUgLmVuYWJsZWQge1xuICAgIGJhY2tncm91bmQ6ICMyOGE3NDU7XG4gICAgYm9yZGVyLWNvbG9yOiAjMWU3YjM0O1xufVxuXG50ZC5uYW1lIGEge1xuICAgIGNvbG9yOiAjMUI2Q0QwO1xuICAgIGZvbnQtd2VpZ2h0OiA1MDA7XG4gICAgdGV4dC1kZWNvcmF0aW9uOiBub25lO1xufVxuXG50ZC5uYW1lIGE6aG92ZXIge1xuICAgIHRleHQtZGVjb3JhdGlvbjogdW5kZXJsaW5lO1xufVxuXG50ZC5ydW5fZXZlcnkge1xuICAgIHRleHQtYWxpZ246IGxlZnQ7XG4gICAgbWluLXdpZHRoOiAxMHJlbTtcbn0iXX0= */"

/***/ }),

/***/ "./src/app/schedule/schedule-list/schedule-list.component.html":
/*!*********************************************************************!*\
  !*** ./src/app/schedule/schedule-list/schedule-list.component.html ***!
  \*********************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"container\">\n    <div class=\"content toolbar\">\n        <div></div>\n        <ul class=\"pagination\">\n            <li class=\"page-item\" (click)=\"goPrevious()\"><button>Previous</button></li>\n            <li class=\"page-item\" (click)=\"goNext()\"><button>Next</button></li>\n        </ul>\n    </div>\n    <div class=\"content table-container\">\n        <table>\n            <thead>\n                <tr>\n                    <th>Name</th>\n                    <th>Language</th>\n                    <th>Last Run</th>\n                    <th>Total Run</th>\n                    <th>Run Every (UTC)</th>\n                </tr>\n            </thead>\n            <tbody>\n                <tr *ngFor=\"let schedule of schedules\">\n                    <td class=\"name\">\n                        <div style=\"display: flex; align-items: center;\">\n                            <div class=\"circle\" [class.enabled]=\"schedule.enabled\"></div>\n                            <a routerLink=\"{{schedule.name}}\">{{schedule.name}}</a>\n                        </div>\n                    </td>\n                    <td>{{schedule.language}}</td>\n                    <td style=\"min-width: 4rem;\">\n                        <span *ngIf=\"schedule.last_run\">{{schedule.last_run | timeAgo}}</span>\n                    </td>\n                    <td><span *ngIf=\"schedule.total_run\">{{schedule.total_run}}</span></td>\n                    <td class=\"run_every\">{{schedule.beat.description()}}</td>\n                </tr>\n            </tbody>\n        </table>\n    </div>\n    <div class=\"content toolbar\">\n        <div></div>\n        <ul class=\"pagination\">\n            <li class=\"page-item\" (click)=\"goPrevious()\"><button>Previous</button></li>\n            <li class=\"page-item\" (click)=\"goNext()\"><button>Next</button></li>\n        </ul>\n    </div>\n</div>"

/***/ }),

/***/ "./src/app/schedule/schedule-list/schedule-list.component.ts":
/*!*******************************************************************!*\
  !*** ./src/app/schedule/schedule-list/schedule-list.component.ts ***!
  \*******************************************************************/
/*! exports provided: ScheduleListComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ScheduleListComponent", function() { return ScheduleListComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var _services_schedules_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../services/schedules.service */ "./src/app/services/schedules.service.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};



var ScheduleListComponent = /** @class */ (function () {
    function ScheduleListComponent(router, schedulesService) {
        this.router = router;
        this.schedulesService = schedulesService;
        this.schedules = [];
    }
    ScheduleListComponent.prototype.ngOnInit = function () {
        var _this = this;
        this.schedulesService.list().subscribe(function (data) {
            _this.schedules = data.items;
            _this.meta = data.meta;
        });
    };
    ScheduleListComponent.prototype.goPrevious = function () {
        var _this = this;
        var skip = Math.max(0, this.meta.skip - 20);
        this.schedulesService.list(skip, 20).subscribe(function (data) {
            _this.schedules = data.items;
            _this.meta = data.meta;
        });
    };
    ScheduleListComponent.prototype.goNext = function () {
        var _this = this;
        this.schedulesService.list(this.meta.skip + 20, 20).subscribe(function (data) {
            _this.schedules = data.items;
            _this.meta = data.meta;
        });
    };
    ScheduleListComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            template: __webpack_require__(/*! ./schedule-list.component.html */ "./src/app/schedule/schedule-list/schedule-list.component.html"),
            styles: [__webpack_require__(/*! ./schedule-list.component.css */ "./src/app/schedule/schedule-list/schedule-list.component.css")]
        }),
        __metadata("design:paramtypes", [_angular_router__WEBPACK_IMPORTED_MODULE_1__["Router"], _services_schedules_service__WEBPACK_IMPORTED_MODULE_2__["SchedulesService"]])
    ], ScheduleListComponent);
    return ScheduleListComponent;
}());



/***/ }),

/***/ "./src/app/schedule/schedule-offliner/schedule-offliner.component.css":
/*!****************************************************************************!*\
  !*** ./src/app/schedule/schedule-offliner/schedule-offliner.component.css ***!
  \****************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IiIsImZpbGUiOiJzcmMvYXBwL3NjaGVkdWxlL3NjaGVkdWxlLW9mZmxpbmVyL3NjaGVkdWxlLW9mZmxpbmVyLmNvbXBvbmVudC5jc3MifQ== */"

/***/ }),

/***/ "./src/app/schedule/schedule-offliner/schedule-offliner.component.html":
/*!*****************************************************************************!*\
  !*** ./src/app/schedule/schedule-offliner/schedule-offliner.component.html ***!
  \*****************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"title\">\n    Offliner\n</div>"

/***/ }),

/***/ "./src/app/schedule/schedule-offliner/schedule-offliner.component.ts":
/*!***************************************************************************!*\
  !*** ./src/app/schedule/schedule-offliner/schedule-offliner.component.ts ***!
  \***************************************************************************/
/*! exports provided: ScheduleOfflinerComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ScheduleOfflinerComponent", function() { return ScheduleOfflinerComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

var ScheduleOfflinerComponent = /** @class */ (function () {
    function ScheduleOfflinerComponent() {
    }
    ScheduleOfflinerComponent.prototype.ngOnInit = function () {
    };
    ScheduleOfflinerComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-schedule-offliner',
            template: __webpack_require__(/*! ./schedule-offliner.component.html */ "./src/app/schedule/schedule-offliner/schedule-offliner.component.html"),
            styles: [__webpack_require__(/*! ./schedule-offliner.component.css */ "./src/app/schedule/schedule-offliner/schedule-offliner.component.css"), __webpack_require__(/*! ../schedule.shared.css */ "./src/app/schedule/schedule.shared.css")]
        }),
        __metadata("design:paramtypes", [])
    ], ScheduleOfflinerComponent);
    return ScheduleOfflinerComponent;
}());



/***/ }),

/***/ "./src/app/schedule/schedule-overview/schedule-overview.component.css":
/*!****************************************************************************!*\
  !*** ./src/app/schedule/schedule-overview/schedule-overview.component.css ***!
  \****************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IiIsImZpbGUiOiJzcmMvYXBwL3NjaGVkdWxlL3NjaGVkdWxlLW92ZXJ2aWV3L3NjaGVkdWxlLW92ZXJ2aWV3LmNvbXBvbmVudC5jc3MifQ== */"

/***/ }),

/***/ "./src/app/schedule/schedule-overview/schedule-overview.component.html":
/*!*****************************************************************************!*\
  !*** ./src/app/schedule/schedule-overview/schedule-overview.component.html ***!
  \*****************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"title\">\n    Overview\n</div>"

/***/ }),

/***/ "./src/app/schedule/schedule-overview/schedule-overview.component.ts":
/*!***************************************************************************!*\
  !*** ./src/app/schedule/schedule-overview/schedule-overview.component.ts ***!
  \***************************************************************************/
/*! exports provided: ScheduleOverviewComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ScheduleOverviewComponent", function() { return ScheduleOverviewComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

var ScheduleOverviewComponent = /** @class */ (function () {
    function ScheduleOverviewComponent() {
    }
    ScheduleOverviewComponent.prototype.ngOnInit = function () {
    };
    ScheduleOverviewComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-schedule-overview',
            template: __webpack_require__(/*! ./schedule-overview.component.html */ "./src/app/schedule/schedule-overview/schedule-overview.component.html"),
            styles: [__webpack_require__(/*! ./schedule-overview.component.css */ "./src/app/schedule/schedule-overview/schedule-overview.component.css"), __webpack_require__(/*! ../schedule.shared.css */ "./src/app/schedule/schedule.shared.css")]
        }),
        __metadata("design:paramtypes", [])
    ], ScheduleOverviewComponent);
    return ScheduleOverviewComponent;
}());



/***/ }),

/***/ "./src/app/schedule/schedule-task/schedule-task.component.css":
/*!********************************************************************!*\
  !*** ./src/app/schedule/schedule-task/schedule-task.component.css ***!
  \********************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IiIsImZpbGUiOiJzcmMvYXBwL3NjaGVkdWxlL3NjaGVkdWxlLXRhc2svc2NoZWR1bGUtdGFzay5jb21wb25lbnQuY3NzIn0= */"

/***/ }),

/***/ "./src/app/schedule/schedule-task/schedule-task.component.html":
/*!*********************************************************************!*\
  !*** ./src/app/schedule/schedule-task/schedule-task.component.html ***!
  \*********************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div class=\"title\">\n    Task\n</div>"

/***/ }),

/***/ "./src/app/schedule/schedule-task/schedule-task.component.ts":
/*!*******************************************************************!*\
  !*** ./src/app/schedule/schedule-task/schedule-task.component.ts ***!
  \*******************************************************************/
/*! exports provided: ScheduleTaskComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ScheduleTaskComponent", function() { return ScheduleTaskComponent; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

var ScheduleTaskComponent = /** @class */ (function () {
    function ScheduleTaskComponent() {
    }
    ScheduleTaskComponent.prototype.ngOnInit = function () {
    };
    ScheduleTaskComponent = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Component"])({
            selector: 'app-schedule-task',
            template: __webpack_require__(/*! ./schedule-task.component.html */ "./src/app/schedule/schedule-task/schedule-task.component.html"),
            styles: [__webpack_require__(/*! ./schedule-task.component.css */ "./src/app/schedule/schedule-task/schedule-task.component.css"), __webpack_require__(/*! ../schedule.shared.css */ "./src/app/schedule/schedule.shared.css")]
        }),
        __metadata("design:paramtypes", [])
    ], ScheduleTaskComponent);
    return ScheduleTaskComponent;
}());



/***/ }),

/***/ "./src/app/schedule/schedule.module.ts":
/*!*********************************************!*\
  !*** ./src/app/schedule/schedule.module.ts ***!
  \*********************************************/
/*! exports provided: ScheduleModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ScheduleModule", function() { return ScheduleModule; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_common__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/common */ "./node_modules/@angular/common/fesm5/common.js");
/* harmony import */ var _angular_router__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/router */ "./node_modules/@angular/router/fesm5/router.js");
/* harmony import */ var _angular_forms__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @angular/forms */ "./node_modules/@angular/forms/fesm5/forms.js");
/* harmony import */ var _shared_shared_module__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../shared/shared.module */ "./src/app/shared/shared.module.ts");
/* harmony import */ var _schedule_list_schedule_list_component__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./schedule-list/schedule-list.component */ "./src/app/schedule/schedule-list/schedule-list.component.ts");
/* harmony import */ var _schedule_detail_schedule_detail_component__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./schedule-detail/schedule-detail.component */ "./src/app/schedule/schedule-detail/schedule-detail.component.ts");
/* harmony import */ var _schedule_overview_schedule_overview_component__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./schedule-overview/schedule-overview.component */ "./src/app/schedule/schedule-overview/schedule-overview.component.ts");
/* harmony import */ var _schedule_beat_schedule_beat_component__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ./schedule-beat/schedule-beat.component */ "./src/app/schedule/schedule-beat/schedule-beat.component.ts");
/* harmony import */ var _schedule_offliner_schedule_offliner_component__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./schedule-offliner/schedule-offliner.component */ "./src/app/schedule/schedule-offliner/schedule-offliner.component.ts");
/* harmony import */ var _schedule_task_schedule_task_component__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ./schedule-task/schedule-task.component */ "./src/app/schedule/schedule-task/schedule-task.component.ts");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};











var routes = [
    { path: '', component: _schedule_list_schedule_list_component__WEBPACK_IMPORTED_MODULE_5__["ScheduleListComponent"] },
    {
        path: ':name',
        component: _schedule_detail_schedule_detail_component__WEBPACK_IMPORTED_MODULE_6__["ScheduleDetailComponent"],
        children: [
            { path: '', component: _schedule_overview_schedule_overview_component__WEBPACK_IMPORTED_MODULE_7__["ScheduleOverviewComponent"] },
            { path: 'beat', component: _schedule_beat_schedule_beat_component__WEBPACK_IMPORTED_MODULE_8__["ScheduleBeatComponent"] },
            { path: 'offliner', component: _schedule_offliner_schedule_offliner_component__WEBPACK_IMPORTED_MODULE_9__["ScheduleOfflinerComponent"] },
            { path: 'task', component: _schedule_task_schedule_task_component__WEBPACK_IMPORTED_MODULE_10__["ScheduleTaskComponent"] },
            { path: '**', redirectTo: '' }
        ]
    }
];
var ScheduleModule = /** @class */ (function () {
    function ScheduleModule() {
    }
    ScheduleModule = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["NgModule"])({
            imports: [
                _angular_common__WEBPACK_IMPORTED_MODULE_1__["CommonModule"],
                _shared_shared_module__WEBPACK_IMPORTED_MODULE_4__["SharedModule"],
                _angular_forms__WEBPACK_IMPORTED_MODULE_3__["FormsModule"],
                _angular_forms__WEBPACK_IMPORTED_MODULE_3__["ReactiveFormsModule"],
                _angular_router__WEBPACK_IMPORTED_MODULE_2__["RouterModule"].forChild(routes)
            ],
            declarations: [
                _schedule_list_schedule_list_component__WEBPACK_IMPORTED_MODULE_5__["ScheduleListComponent"],
                _schedule_detail_schedule_detail_component__WEBPACK_IMPORTED_MODULE_6__["ScheduleDetailComponent"],
                _schedule_overview_schedule_overview_component__WEBPACK_IMPORTED_MODULE_7__["ScheduleOverviewComponent"],
                _schedule_beat_schedule_beat_component__WEBPACK_IMPORTED_MODULE_8__["ScheduleBeatComponent"],
                _schedule_offliner_schedule_offliner_component__WEBPACK_IMPORTED_MODULE_9__["ScheduleOfflinerComponent"],
                _schedule_task_schedule_task_component__WEBPACK_IMPORTED_MODULE_10__["ScheduleTaskComponent"]
            ]
        })
    ], ScheduleModule);
    return ScheduleModule;
}());



/***/ }),

/***/ "./src/app/schedule/schedule.shared.css":
/*!**********************************************!*\
  !*** ./src/app/schedule/schedule.shared.css ***!
  \**********************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".title {\n    font-size: 2rem;\n    padding: 0 0.5rem;\n    border-bottom: 1.5px #e7e7e7 solid;\n}\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInNyYy9hcHAvc2NoZWR1bGUvc2NoZWR1bGUuc2hhcmVkLmNzcyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQTtJQUNJLGdCQUFnQjtJQUNoQixrQkFBa0I7SUFDbEIsbUNBQW1DO0NBQ3RDIiwiZmlsZSI6InNyYy9hcHAvc2NoZWR1bGUvc2NoZWR1bGUuc2hhcmVkLmNzcyIsInNvdXJjZXNDb250ZW50IjpbIi50aXRsZSB7XG4gICAgZm9udC1zaXplOiAycmVtO1xuICAgIHBhZGRpbmc6IDAgMC41cmVtO1xuICAgIGJvcmRlci1ib3R0b206IDEuNXB4ICNlN2U3ZTcgc29saWQ7XG59Il19 */"

/***/ }),

/***/ "./src/app/services/const.service.ts":
/*!*******************************************!*\
  !*** ./src/app/services/const.service.ts ***!
  \*******************************************/
/*! exports provided: languageNames, apiRoot */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "languageNames", function() { return languageNames; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "apiRoot", function() { return apiRoot; });
var languageNames = { 'aaa': 'Ghotuo', 'aab': 'Alumu-Tesu', 'aac': 'Ari', 'aad': 'Amal', 'aae': 'Arbëreshë Albanian', 'aaf': 'Aranadan', 'aag': 'Ambrak', 'aah': "Abu' Arapesh", 'aai': 'Arifama-Miniafia', 'aak': 'Ankave', 'aal': 'Afade', 'aan': 'Anambé', 'aao': 'Algerian Saharan Arabic', 'aap': 'Pará Arára', 'aaq': 'Eastern Abnaki', 'aar': 'Afar', 'aas': 'Aasáx', 'aat': 'Arvanitika Albanian', 'aau': 'Abau', 'aaw': 'Solong', 'aax': 'Mandobo Atas', 'aaz': 'Amarasi', 'aba': 'Abé', 'abb': 'Bankon', 'abc': 'Ambala Ayta', 'abd': 'Manide', 'abe': 'Western Abnaki', 'abf': 'Abai Sungai', 'abg': 'Abaga', 'abh': 'Tajiki Arabic', 'abi': 'Abidji', 'abj': 'Aka-Bea', 'abk': 'Abkhazian', 'abl': 'Lampung Nyo', 'abm': 'Abanyom', 'abn': 'Abua', 'abo': 'Abon', 'abp': 'Abellen Ayta', 'abq': 'Abaza', 'abr': 'Abron', 'abs': 'Ambonese Malay', 'abt': 'Ambulas', 'abu': 'Abure', 'abv': 'Baharna Arabic', 'abw': 'Pal', 'abx': 'Inabaknon', 'aby': 'Aneme Wake', 'abz': 'Abui', 'aca': 'Achagua', 'acb': 'Áncá', 'acd': 'Gikyode', 'ace': 'Achinese', 'acf': 'Saint Lucian Creole French', 'ach': 'Acoli', 'aci': 'Aka-Cari', 'ack': 'Aka-Kora', 'acl': 'Akar-Bale', 'acm': 'Mesopotamian Arabic', 'acn': 'Achang', 'acp': 'Eastern Acipa', 'acq': "Ta'izzi-Adeni Arabic", 'acr': 'Achi', 'acs': 'Acroá', 'act': 'Achterhoeks', 'acu': 'Achuar-Shiwiar', 'acv': 'Achumawi', 'acw': 'Hijazi Arabic', 'acx': 'Omani Arabic', 'acy': 'Cypriot Arabic', 'acz': 'Acheron', 'ada': 'Adangme', 'adb': 'Adabe', 'add': 'Dzodinka', 'ade': 'Adele', 'adf': 'Dhofari Arabic', 'adg': 'Andegerebinha', 'adh': 'Adhola', 'adi': 'Adi', 'adj': 'Adioukrou', 'adl': 'Galo', 'adn': 'Adang', 'ado': 'Abu', 'adq': 'Adangbe', 'adr': 'Adonara', 'ads': 'Adamorobe Sign Language', 'adt': 'Adnyamathanha', 'adu': 'Aduge', 'adw': 'Amundava', 'adx': 'Amdo Tibetan', 'ady': 'Adyghe', 'adz': 'Adzera', 'aea': 'Areba', 'aeb': 'Tunisian Arabic', 'aec': 'Saidi Arabic', 'aed': 'Argentine Sign Language', 'aee': 'Northeast Pashai', 'aek': 'Haeke', 'ael': 'Ambele', 'aem': 'Arem', 'aen': 'Armenian Sign Language', 'aeq': 'Aer', 'aer': 'Eastern Arrernte', 'aes': 'Alsea', 'aeu': 'Akeu', 'aew': 'Ambakich', 'aey': 'Amele', 'aez': 'Aeka', 'afb': 'Gulf Arabic', 'afd': 'Andai', 'afe': 'Putukwam', 'afg': 'Afghan Sign Language', 'afh': 'Afrihili', 'afi': 'Akrukay', 'afk': 'Nanubae', 'afn': 'Defaka', 'afo': 'Eloyi', 'afp': 'Tapei', 'afr': 'Afrikaans', 'afs': 'Afro-Seminole Creole', 'aft': 'Afitti', 'afu': 'Awutu', 'afz': 'Obokuitai', 'aga': 'Aguano', 'agb': 'Legbo', 'agc': 'Agatu', 'agd': 'Agarabi', 'age': 'Angal', 'agf': 'Arguni', 'agg': 'Angor', 'agh': 'Ngelima', 'agi': 'Agariya', 'agj': 'Argobba', 'agk': 'Isarog Agta', 'agl': 'Fembe', 'agm': 'Angaataha', 'agn': 'Agutaynen', 'ago': 'Tainae', 'agq': 'Aghem', 'agr': 'Aguaruna', 'ags': 'Esimbi', 'agt': 'Central Cagayan Agta', 'agu': 'Aguacateco', 'agv': 'Remontado Dumagat', 'agw': 'Kahua', 'agx': 'Aghul', 'agy': 'Southern Alta', 'agz': 'Mt. Iriga Agta', 'aha': 'Ahanta', 'ahb': 'Axamb', 'ahg': 'Qimant', 'ahh': 'Aghu', 'ahi': 'Tiagbamrin Aizi', 'ahk': 'Akha', 'ahl': 'Igo', 'ahm': 'Mobumrin Aizi', 'ahn': 'Àhàn', 'aho': 'Ahom', 'ahp': 'Aproumu Aizi', 'ahr': 'Ahirani', 'ahs': 'Ashe', 'aht': 'Ahtena', 'aia': 'Arosi', 'aib': 'Ainu (China)', 'aic': 'Ainbai', 'aid': 'Alngith', 'aie': 'Amara', 'aif': 'Agi', 'aig': 'Antigua and Barbuda Creole English', 'aih': 'Ai-Cham', 'aii': 'Assyrian Neo-Aramaic', 'aij': 'Lishanid Noshan', 'aik': 'Ake', 'ail': 'Aimele', 'aim': 'Aimol', 'ain': 'Ainu (Japan)', 'aio': 'Aiton', 'aip': 'Burumakok', 'aiq': 'Aimaq', 'air': 'Airoran', 'ais': 'Nataoran Amis', 'ait': 'Arikem', 'aiw': 'Aari', 'aix': 'Aighon', 'aiy': 'Ali', 'aja': 'Aja (Sudan)', 'ajg': 'Aja (Benin)', 'aji': 'Ajië', 'ajn': 'Andajin', 'ajp': 'South Levantine Arabic', 'ajt': 'Judeo-Tunisian Arabic', 'aju': 'Judeo-Moroccan Arabic', 'ajw': 'Ajawa', 'ajz': 'Amri Karbi', 'aka': 'Akan', 'akb': 'Batak Angkola', 'akc': 'Mpur', 'akd': 'Ukpet-Ehom', 'ake': 'Akawaio', 'akf': 'Akpa', 'akg': 'Anakalangu', 'akh': 'Angal Heneng', 'aki': 'Aiome', 'akj': 'Aka-Jeru', 'akk': 'Akkadian', 'akl': 'Aklanon', 'akm': 'Aka-Bo', 'ako': 'Akurio', 'akp': 'Siwu', 'akq': 'Ak', 'akr': 'Araki', 'aks': 'Akaselem', 'akt': 'Akolet', 'aku': 'Akum', 'akv': 'Akhvakh', 'akw': 'Akwa', 'akx': 'Aka-Kede', 'aky': 'Aka-Kol', 'akz': 'Alabama', 'ala': 'Alago', 'alc': 'Qawasqar', 'ald': 'Alladian', 'ale': 'Aleut', 'alf': 'Alege', 'alh': 'Alawa', 'ali': 'Amaimon', 'alj': 'Alangan', 'alk': 'Alak', 'all': 'Allar', 'alm': 'Amblong', 'aln': 'Gheg Albanian', 'alo': 'Larike-Wakasihu', 'alp': 'Alune', 'alq': 'Algonquin', 'alr': 'Alutor', 'als': 'Tosk Albanian', 'alt': 'Southern Altai', 'alu': "'Are'are", 'alw': 'Alaba-K’abeena', 'alx': 'Amol', 'aly': 'Alyawarr', 'alz': 'Alur', 'ama': 'Amanayé', 'amb': 'Ambo', 'amc': 'Amahuaca', 'ame': "Yanesha'", 'amf': 'Hamer-Banna', 'amg': 'Amurdak', 'amh': 'Amharic', 'ami': 'Amis', 'amj': 'Amdang', 'amk': 'Ambai', 'aml': 'War-Jaintia', 'amm': 'Ama (Papua New Guinea)', 'amn': 'Amanab', 'amo': 'Amo', 'amp': 'Alamblak', 'amq': 'Amahai', 'amr': 'Amarakaeri', 'ams': 'Southern Amami-Oshima', 'amt': 'Amto', 'amu': 'Guerrero Amuzgo', 'amv': 'Ambelau', 'amw': 'Western Neo-Aramaic', 'amx': 'Anmatyerre', 'amy': 'Ami', 'amz': 'Atampaya', 'ana': 'Andaqui', 'anb': 'Andoa', 'anc': 'Ngas', 'and': 'Ansus', 'ane': 'Xârâcùù', 'anf': 'Animere', 'ang': 'Old English (ca. 450-1100)', 'anh': 'Nend', 'ani': 'Andi', 'anj': 'Anor', 'ank': 'Goemai', 'anl': 'Anu-Hkongso Chin', 'anm': 'Anal', 'ann': 'Obolo', 'ano': 'Andoque', 'anp': 'Angika', 'anq': 'Jarawa (India)', 'anr': 'Andh', 'ans': 'Anserma', 'ant': 'Antakarinya', 'anu': 'Anuak', 'anv': 'Denya', 'anw': 'Anaang', 'anx': 'Andra-Hus', 'any': 'Anyin', 'anz': 'Anem', 'aoa': 'Angolar', 'aob': 'Abom', 'aoc': 'Pemon', 'aod': 'Andarum', 'aoe': 'Angal Enen', 'aof': 'Bragat', 'aog': 'Angoram', 'aoh': 'Arma', 'aoi': 'Anindilyakwa', 'aoj': 'Mufian', 'aok': 'Arhö', 'aol': 'Alor', 'aom': 'Ömie', 'aon': 'Bumbita Arapesh', 'aor': 'Aore', 'aos': 'Taikat', 'aot': 'Atong (India)', 'aou': "A'ou", 'aox': 'Atorada', 'aoz': 'Uab Meto', 'apb': "Sa'a", 'apc': 'North Levantine Arabic', 'apd': 'Sudanese Arabic', 'ape': 'Bukiyip', 'apf': 'Pahanan Agta', 'apg': 'Ampanang', 'aph': 'Athpariya', 'api': 'Apiaká', 'apj': 'Jicarilla Apache', 'apk': 'Kiowa Apache', 'apl': 'Lipan Apache', 'apm': 'Mescalero-Chiricahua Apache', 'apn': 'Apinayé', 'apo': 'Ambul', 'app': 'Apma', 'apq': 'A-Pucikwar', 'apr': 'Arop-Lokep', 'aps': 'Arop-Sissano', 'apt': 'Apatani', 'apu': 'Apurinã', 'apv': 'Alapmunte', 'apw': 'Western Apache', 'apx': 'Aputai', 'apy': 'Apalaí', 'apz': 'Safeyoka', 'aqc': 'Archi', 'aqd': 'Ampari Dogon', 'aqg': 'Arigidi', 'aqm': 'Atohwaim', 'aqn': 'Northern Alta', 'aqp': 'Atakapa', 'aqr': 'Arhâ', 'aqt': 'Angaité', 'aqz': 'Akuntsu', 'ara': 'Arabic', 'arb': 'Standard Arabic', 'arc': 'Official Aramaic (700-300 BCE)', 'ard': 'Arabana', 'are': 'Western Arrarnta', 'arg': 'Aragonese', 'arh': 'Arhuaco', 'ari': 'Arikara', 'arj': 'Arapaso', 'ark': 'Arikapú', 'arl': 'Arabela', 'arn': 'Mapudungun', 'aro': 'Araona', 'arp': 'Arapaho', 'arq': 'Algerian Arabic', 'arr': 'Karo (Brazil)', 'ars': 'Najdi Arabic', 'aru': 'Aruá (Amazonas State)', 'arv': 'Arbore', 'arw': 'Arawak', 'arx': 'Aruá (Rodonia State)', 'ary': 'Moroccan Arabic', 'arz': 'Egyptian Arabic', 'asa': 'Asu (Tanzania)', 'asb': 'Assiniboine', 'asc': 'Casuarina Coast Asmat', 'asd': 'Asas', 'ase': 'American Sign Language', 'asf': 'Australian Sign Language', 'asg': 'Cishingini', 'ash': 'Abishira', 'asi': 'Buruwai', 'asj': 'Sari', 'ask': 'Ashkun', 'asl': 'Asilulu', 'asm': 'Assamese', 'asn': 'Xingú Asuriní', 'aso': 'Dano', 'asp': 'Algerian Sign Language', 'asq': 'Austrian Sign Language', 'asr': 'Asuri', 'ass': 'Ipulo', 'ast': 'Asturian', 'asu': 'Tocantins Asurini', 'asv': 'Asoa', 'asw': 'Australian Aborigines Sign Language', 'asx': 'Muratayak', 'asy': 'Yaosakor Asmat', 'asz': 'As', 'ata': 'Pele-Ata', 'atb': 'Zaiwa', 'atc': 'Atsahuaca', 'atd': 'Ata Manobo', 'ate': 'Atemble', 'atg': 'Ivbie North-Okpela-Arhe', 'ati': 'Attié', 'atj': 'Atikamekw', 'atk': 'Ati', 'atl': 'Mt. Iraya Agta', 'atm': 'Ata', 'atn': 'Ashtiani', 'ato': 'Atong (Cameroon)', 'atp': 'Pudtol Atta', 'atq': 'Aralle-Tabulahan', 'atr': 'Waimiri-Atroari', 'ats': 'Gros Ventre', 'att': 'Pamplona Atta', 'atu': 'Reel', 'atv': 'Northern Altai', 'atw': 'Atsugewi', 'atx': 'Arutani', 'aty': 'Aneityum', 'atz': 'Arta', 'aua': 'Asumboa', 'aub': 'Alugu', 'auc': 'Waorani', 'aud': 'Anuta', 'aug': 'Aguna', 'auh': 'Aushi', 'aui': 'Anuki', 'auj': 'Awjilah', 'auk': 'Heyo', 'aul': 'Aulua', 'aum': 'Asu (Nigeria)', 'aun': 'Molmo One', 'auo': 'Auyokawa', 'aup': 'Makayam', 'auq': 'Anus', 'aur': 'Aruek', 'aut': 'Austral', 'auu': 'Auye', 'auw': 'Awyi', 'aux': 'Aurá', 'auy': 'Awiyaana', 'auz': 'Uzbeki Arabic', 'ava': 'Avaric', 'avb': 'Avau', 'avd': 'Alviri-Vidari', 'ave': 'Avestan', 'avi': 'Avikam', 'avk': 'Kotava', 'avl': 'Eastern Egyptian Bedawi Arabic', 'avm': 'Angkamuthi', 'avn': 'Avatime', 'avo': 'Agavotaguerra', 'avs': 'Aushiri', 'avt': 'Au', 'avu': 'Avokaya', 'avv': 'Avá-Canoeiro', 'awa': 'Awadhi', 'awb': 'Awa (Papua New Guinea)', 'awc': 'Cicipu', 'awe': 'Awetí', 'awg': 'Anguthimri', 'awh': 'Awbono', 'awi': 'Aekyom', 'awk': 'Awabakal', 'awm': 'Arawum', 'awn': 'Awngi', 'awo': 'Awak', 'awr': 'Awera', 'aws': 'South Awyu', 'awt': 'Araweté', 'awu': 'Central Awyu', 'awv': 'Jair Awyu', 'aww': 'Awun', 'awx': 'Awara', 'awy': 'Edera Awyu', 'axb': 'Abipon', 'axe': 'Ayerrerenge', 'axg': 'Mato Grosso Arára', 'axk': 'Yaka (Central African Republic)', 'axl': 'Lower Southern Aranda', 'axm': 'Middle Armenian', 'axx': 'Xârâgurè', 'aya': 'Awar', 'ayb': 'Ayizo Gbe', 'ayc': 'Southern Aymara', 'ayd': 'Ayabadhu', 'aye': 'Ayere', 'ayg': 'Ginyanga', 'ayh': 'Hadrami Arabic', 'ayi': 'Leyigha', 'ayk': 'Akuku', 'ayl': 'Libyan Arabic', 'aym': 'Aymara', 'ayn': 'Sanaani Arabic', 'ayo': 'Ayoreo', 'ayp': 'North Mesopotamian Arabic', 'ayq': 'Ayi (Papua New Guinea)', 'ayr': 'Central Aymara', 'ays': 'Sorsogon Ayta', 'ayt': 'Magbukun Ayta', 'ayu': 'Ayu', 'ayy': 'Tayabas Ayta', 'ayz': 'Mai Brat', 'aza': 'Azha', 'azb': 'South Azerbaijani', 'azd': 'Eastern Durango Nahuatl', 'aze': 'Azerbaijani', 'azg': 'San Pedro Amuzgos Amuzgo', 'azj': 'North Azerbaijani', 'azm': 'Ipalapa Amuzgo', 'azn': 'Western Durango Nahuatl', 'azo': 'Awing', 'azt': 'Faire Atta', 'azz': 'Highland Puebla Nahuatl', 'baa': 'Babatana', 'bab': 'Bainouk-Gunyuño', 'bac': 'Badui', 'bae': 'Baré', 'baf': 'Nubaca', 'bag': 'Tuki', 'bah': 'Bahamas Creole English', 'baj': 'Barakai', 'bak': 'Bashkir', 'bal': 'Baluchi', 'bam': 'Bambara', 'ban': 'Balinese', 'bao': 'Waimaha', 'bap': 'Bantawa', 'bar': 'Bavarian', 'bas': 'Basa (Cameroon)', 'bau': 'Bada (Nigeria)', 'bav': 'Vengo', 'baw': 'Bambili-Bambui', 'bax': 'Bamun', 'bay': 'Batuley', 'bba': 'Baatonum', 'bbb': 'Barai', 'bbc': 'Batak Toba', 'bbd': 'Bau', 'bbe': 'Bangba', 'bbf': 'Baibai', 'bbg': 'Barama', 'bbh': 'Bugan', 'bbi': 'Barombi', 'bbj': "Ghomálá'", 'bbk': 'Babanki', 'bbl': 'Bats', 'bbm': 'Babango', 'bbn': 'Uneapa', 'bbo': 'Northern Bobo Madaré', 'bbp': 'West Central Banda', 'bbq': 'Bamali', 'bbr': 'Girawa', 'bbs': 'Bakpinka', 'bbt': 'Mburku', 'bbu': 'Kulung (Nigeria)', 'bbv': 'Karnai', 'bbw': 'Baba', 'bbx': 'Bubia', 'bby': 'Befang', 'bbz': 'Babalia Creole Arabic', 'bca': 'Central Bai', 'bcb': 'Bainouk-Samik', 'bcc': 'Southern Balochi', 'bcd': 'North Babar', 'bce': 'Bamenyam', 'bcf': 'Bamu', 'bcg': 'Baga Pokur', 'bch': 'Bariai', 'bci': 'Baoulé', 'bcj': 'Bardi', 'bck': 'Bunaba', 'bcl': 'Central Bikol', 'bcm': 'Bannoni', 'bcn': 'Bali (Nigeria)', 'bco': 'Kaluli', 'bcp': 'Bali (Democratic Republic of Congo)', 'bcq': 'Bench', 'bcr': 'Babine', 'bcs': 'Kohumono', 'bct': 'Bendi', 'bcu': 'Awad Bing', 'bcv': 'Shoo-Minda-Nye', 'bcw': 'Bana', 'bcy': 'Bacama', 'bcz': 'Bainouk-Gunyaamolo', 'bda': 'Bayot', 'bdb': 'Basap', 'bdc': 'Emberá-Baudó', 'bdd': 'Bunama', 'bde': 'Bade', 'bdf': 'Biage', 'bdg': 'Bonggi', 'bdh': 'Baka (Sudan)', 'bdi': 'Burun', 'bdj': 'Bai', 'bdk': 'Budukh', 'bdl': 'Indonesian Bajau', 'bdm': 'Buduma', 'bdn': 'Baldemu', 'bdo': 'Morom', 'bdp': 'Bende', 'bdq': 'Bahnar', 'bdr': 'West Coast Bajau', 'bds': 'Burunge', 'bdt': 'Bokoto', 'bdu': 'Oroko', 'bdv': 'Bodo Parja', 'bdw': 'Baham', 'bdx': 'Budong-Budong', 'bdy': 'Bandjalang', 'bdz': 'Badeshi', 'bea': 'Beaver', 'beb': 'Bebele', 'bec': 'Iceve-Maci', 'bed': 'Bedoanas', 'bee': 'Byangsi', 'bef': 'Benabena', 'beg': 'Belait', 'beh': 'Biali', 'bei': "Bekati'", 'bej': 'Beja', 'bek': 'Bebeli', 'bel': 'Belarusian', 'bem': 'Bemba (Zambia)', 'ben': 'Bengali', 'beo': 'Beami', 'bep': 'Besoa', 'beq': 'Beembe', 'bes': 'Besme', 'bet': 'Guiberoua Béte', 'beu': 'Blagar', 'bev': 'Daloa Bété', 'bew': 'Betawi', 'bex': 'Jur Modo', 'bey': 'Beli (Papua New Guinea)', 'bez': 'Bena (Tanzania)', 'bfa': 'Bari', 'bfb': 'Pauri Bareli', 'bfc': 'Panyi Bai', 'bfd': 'Bafut', 'bfe': 'Betaf', 'bff': 'Bofi', 'bfg': 'Busang Kayan', 'bfh': 'Blafe', 'bfi': 'British Sign Language', 'bfj': 'Bafanji', 'bfk': 'Ban Khor Sign Language', 'bfl': 'Banda-Ndélé', 'bfm': 'Mmen', 'bfn': 'Bunak', 'bfo': 'Malba Birifor', 'bfp': 'Beba', 'bfq': 'Badaga', 'bfr': 'Bazigar', 'bfs': 'Southern Bai', 'bft': 'Balti', 'bfu': 'Gahri', 'bfw': 'Bondo', 'bfx': 'Bantayanon', 'bfy': 'Bagheli', 'bfz': 'Mahasu Pahari', 'bga': 'Gwamhi-Wuri', 'bgb': 'Bobongko', 'bgc': 'Haryanvi', 'bgd': 'Rathwi Bareli', 'bge': 'Bauria', 'bgf': 'Bangandu', 'bgg': 'Bugun', 'bgi': 'Giangan', 'bgj': 'Bangolan', 'bgk': 'Bit', 'bgl': 'Bo (Laos)', 'bgn': 'Western Balochi', 'bgo': 'Baga Koga', 'bgp': 'Eastern Balochi', 'bgq': 'Bagri', 'bgr': 'Bawm Chin', 'bgs': 'Tagabawa', 'bgt': 'Bughotu', 'bgu': 'Mbongno', 'bgv': 'Warkay-Bipim', 'bgw': 'Bhatri', 'bgx': 'Balkan Gagauz Turkish', 'bgy': 'Benggoi', 'bgz': 'Banggai', 'bha': 'Bharia', 'bhb': 'Bhili', 'bhc': 'Biga', 'bhd': 'Bhadrawahi', 'bhe': 'Bhaya', 'bhf': 'Odiai', 'bhg': 'Binandere', 'bhh': 'Bukharic', 'bhi': 'Bhilali', 'bhj': 'Bahing', 'bhl': 'Bimin', 'bhm': 'Bathari', 'bhn': 'Bohtan Neo-Aramaic', 'bho': 'Bhojpuri', 'bhp': 'Bima', 'bhq': 'Tukang Besi South', 'bhr': 'Bara Malagasy', 'bhs': 'Buwal', 'bht': 'Bhattiyali', 'bhu': 'Bhunjia', 'bhv': 'Bahau', 'bhw': 'Biak', 'bhx': 'Bhalay', 'bhy': 'Bhele', 'bhz': 'Bada (Indonesia)', 'bia': 'Badimaya', 'bib': 'Bissa', 'bic': 'Bikaru', 'bid': 'Bidiyo', 'bie': 'Bepour', 'bif': 'Biafada', 'big': 'Biangai', 'bij': 'Vaghat-Ya-Bijim-Legeri', 'bik': 'Bikol', 'bil': 'Bile', 'bim': 'Bimoba', 'bin': 'Bini', 'bio': 'Nai', 'bip': 'Bila', 'biq': 'Bipi', 'bir': 'Bisorio', 'bis': 'Bislama', 'bit': 'Berinomo', 'biu': 'Biete', 'biv': 'Southern Birifor', 'biw': 'Kol (Cameroon)', 'bix': 'Bijori', 'biy': 'Birhor', 'biz': 'Baloi', 'bja': 'Budza', 'bjb': 'Banggarla', 'bjc': 'Bariji', 'bje': 'Biao-Jiao Mien', 'bjf': 'Barzani Jewish Neo-Aramaic', 'bjg': 'Bidyogo', 'bjh': 'Bahinemo', 'bji': 'Burji', 'bjj': 'Kanauji', 'bjk': 'Barok', 'bjl': 'Bulu (Papua New Guinea)', 'bjm': 'Bajelani', 'bjn': 'Banjar', 'bjo': 'Mid-Southern Banda', 'bjp': 'Fanamaket', 'bjr': 'Binumarien', 'bjs': 'Bajan', 'bjt': 'Balanta-Ganja', 'bju': 'Busuu', 'bjv': 'Bedjond', 'bjw': 'Bakwé', 'bjx': 'Banao Itneg', 'bjy': 'Bayali', 'bjz': 'Baruga', 'bka': 'Kyak', 'bkc': 'Baka (Cameroon)', 'bkd': 'Binukid', 'bkf': 'Beeke', 'bkg': 'Buraka', 'bkh': 'Bakoko', 'bki': 'Baki', 'bkj': 'Pande', 'bkk': 'Brokskat', 'bkl': 'Berik', 'bkm': 'Kom (Cameroon)', 'bkn': 'Bukitan', 'bko': "Kwa'", 'bkp': 'Boko (Democratic Republic of Congo)', 'bkq': 'Bakairí', 'bkr': 'Bakumpai', 'bks': 'Northern Sorsoganon', 'bkt': 'Boloki', 'bku': 'Buhid', 'bkv': 'Bekwarra', 'bkw': 'Bekwel', 'bkx': 'Baikeno', 'bky': 'Bokyi', 'bkz': 'Bungku', 'bla': 'Siksika', 'blb': 'Bilua', 'blc': 'Bella Coola', 'bld': 'Bolango', 'ble': 'Balanta-Kentohe', 'blf': 'Buol', 'blg': 'Balau', 'blh': 'Kuwaa', 'bli': 'Bolia', 'blj': 'Bolongan', 'blk': "Pa'o Karen", 'bll': 'Biloxi', 'blm': 'Beli (Sudan)', 'bln': 'Southern Catanduanes Bikol', 'blo': 'Anii', 'blp': 'Blablanga', 'blq': 'Baluan-Pam', 'blr': 'Blang', 'bls': 'Balaesang', 'blt': 'Tai Dam', 'blv': 'Bolo', 'blw': 'Balangao', 'blx': 'Mag-Indi Ayta', 'bly': 'Notre', 'blz': 'Balantak', 'bma': 'Lame', 'bmb': 'Bembe', 'bmc': 'Biem', 'bmd': 'Baga Manduri', 'bme': 'Limassa', 'bmf': 'Bom', 'bmg': 'Bamwe', 'bmh': 'Kein', 'bmi': 'Bagirmi', 'bmj': 'Bote-Majhi', 'bmk': 'Ghayavi', 'bml': 'Bomboli', 'bmm': 'Northern Betsimisaraka Malagasy', 'bmn': 'Bina (Papua New Guinea)', 'bmo': 'Bambalang', 'bmp': 'Bulgebi', 'bmq': 'Bomu', 'bmr': 'Muinane', 'bms': 'Bilma Kanuri', 'bmt': 'Biao Mon', 'bmu': 'Somba-Siawari', 'bmv': 'Bum', 'bmw': 'Bomwali', 'bmx': 'Baimak', 'bmz': 'Baramu', 'bna': 'Bonerate', 'bnb': 'Bookan', 'bnc': 'Bontok', 'bnd': 'Banda (Indonesia)', 'bne': 'Bintauna', 'bnf': 'Masiwang', 'bng': 'Benga', 'bni': 'Bangi', 'bnj': 'Eastern Tawbuid', 'bnk': 'Bierebo', 'bnl': 'Boon', 'bnm': 'Batanga', 'bnn': 'Bunun', 'bno': 'Bantoanon', 'bnp': 'Bola', 'bnq': 'Bantik', 'bnr': 'Butmas-Tur', 'bns': 'Bundeli', 'bnu': 'Bentong', 'bnv': 'Bonerif', 'bnw': 'Bisis', 'bnx': 'Bangubangu', 'bny': 'Bintulu', 'bnz': 'Beezen', 'boa': 'Bora', 'bob': 'Aweer', 'bod': 'Tibetan', 'boe': 'Mundabli', 'bof': 'Bolon', 'bog': 'Bamako Sign Language', 'boh': 'Boma', 'boi': 'Barbareño', 'boj': 'Anjam', 'bok': 'Bonjo', 'bol': 'Bole', 'bom': 'Berom', 'bon': 'Bine', 'boo': 'Tiemacèwè Bozo', 'bop': 'Bonkiman', 'boq': 'Bogaya', 'bor': 'Borôro', 'bos': 'Bosnian', 'bot': 'Bongo', 'bou': 'Bondei', 'bov': 'Tuwuli', 'bow': 'Rema', 'box': 'Buamu', 'boy': 'Bodo (Central African Republic)', 'boz': 'Tiéyaxo Bozo', 'bpa': 'Daakaka', 'bpb': 'Barbacoas', 'bpd': 'Banda-Banda', 'bpg': 'Bonggo', 'bph': 'Botlikh', 'bpi': 'Bagupi', 'bpj': 'Binji', 'bpk': 'Orowe', 'bpl': 'Broome Pearling Lugger Pidgin', 'bpm': 'Biyom', 'bpn': 'Dzao Min', 'bpo': 'Anasi', 'bpp': 'Kaure', 'bpq': 'Banda Malay', 'bpr': 'Koronadal Blaan', 'bps': 'Sarangani Blaan', 'bpt': 'Barrow Point', 'bpu': 'Bongu', 'bpv': 'Bian Marind', 'bpw': 'Bo (Papua New Guinea)', 'bpx': 'Palya Bareli', 'bpy': 'Bishnupriya', 'bpz': 'Bilba', 'bqa': 'Tchumbuli', 'bqb': 'Bagusa', 'bqc': 'Boko (Benin)', 'bqd': 'Bung', 'bqf': 'Baga Kaloum', 'bqg': 'Bago-Kusuntu', 'bqh': 'Baima', 'bqi': 'Bakhtiari', 'bqj': 'Bandial', 'bqk': 'Banda-Mbrès', 'bql': 'Bilakura', 'bqm': 'Wumboko', 'bqn': 'Bulgarian Sign Language', 'bqo': 'Balo', 'bqp': 'Busa', 'bqq': 'Biritai', 'bqr': 'Burusu', 'bqs': 'Bosngun', 'bqt': 'Bamukumbit', 'bqu': 'Boguru', 'bqv': 'Koro Wachi', 'bqw': 'Buru (Nigeria)', 'bqx': 'Baangi', 'bqy': 'Bengkala Sign Language', 'bqz': 'Bakaka', 'bra': 'Braj', 'brb': 'Lave', 'brc': 'Berbice Creole Dutch', 'brd': 'Baraamu', 'bre': 'Breton', 'brf': 'Bera', 'brg': 'Baure', 'brh': 'Brahui', 'bri': 'Mokpwe', 'brj': 'Bieria', 'brk': 'Birked', 'brl': 'Birwa', 'brm': 'Barambu', 'brn': 'Boruca', 'bro': 'Brokkat', 'brp': 'Barapasi', 'brq': 'Breri', 'brr': 'Birao', 'brs': 'Baras', 'brt': 'Bitare', 'bru': 'Eastern Bru', 'brv': 'Western Bru', 'brw': 'Bellari', 'brx': 'Bodo (India)', 'bry': 'Burui', 'brz': 'Bilbil', 'bsa': 'Abinomn', 'bsb': 'Brunei Bisaya', 'bsc': 'Bassari', 'bse': 'Wushi', 'bsf': 'Bauchi', 'bsg': 'Bashkardi', 'bsh': 'Kati', 'bsi': 'Bassossi', 'bsj': 'Bangwinji', 'bsk': 'Burushaski', 'bsl': 'Basa-Gumna', 'bsm': 'Busami', 'bsn': 'Barasana-Eduria', 'bso': 'Buso', 'bsp': 'Baga Sitemu', 'bsq': 'Bassa', 'bsr': 'Bassa-Kontagora', 'bss': 'Akoose', 'bst': 'Basketo', 'bsu': 'Bahonsuai', 'bsv': 'Baga Sobané', 'bsw': 'Baiso', 'bsx': 'Yangkam', 'bsy': 'Sabah Bisaya', 'bta': 'Bata', 'btc': 'Bati (Cameroon)', 'btd': 'Batak Dairi', 'bte': 'Gamo-Ningi', 'btf': 'Birgit', 'btg': 'Gagnoa Bété', 'bth': 'Biatah Bidayuh', 'bti': 'Burate', 'btj': 'Bacanese Malay', 'btm': 'Batak Mandailing', 'btn': 'Ratagnon', 'bto': 'Rinconada Bikol', 'btp': 'Budibud', 'btq': 'Batek', 'btr': 'Baetora', 'bts': 'Batak Simalungun', 'btt': 'Bete-Bendi', 'btu': 'Batu', 'btv': 'Bateri', 'btw': 'Butuanon', 'btx': 'Batak Karo', 'bty': 'Bobot', 'btz': 'Batak Alas-Kluet', 'bua': 'Buriat', 'bub': 'Bua', 'buc': 'Bushi', 'bud': 'Ntcham', 'bue': 'Beothuk', 'buf': 'Bushoong', 'bug': 'Buginese', 'buh': 'Younuo Bunu', 'bui': 'Bongili', 'buj': 'Basa-Gurmana', 'buk': 'Bugawac', 'bul': 'Bulgarian', 'bum': 'Bulu (Cameroon)', 'bun': 'Sherbro', 'buo': 'Terei', 'bup': 'Busoa', 'buq': 'Brem', 'bus': 'Bokobaru', 'but': 'Bungain', 'buu': 'Budu', 'buv': 'Bun', 'buw': 'Bubi', 'bux': 'Boghom', 'buy': 'Bullom So', 'buz': 'Bukwen', 'bva': 'Barein', 'bvb': 'Bube', 'bvc': 'Baelelea', 'bvd': 'Baeggu', 'bve': 'Berau Malay', 'bvf': 'Boor', 'bvg': 'Bonkeng', 'bvh': 'Bure', 'bvi': 'Belanda Viri', 'bvj': 'Baan', 'bvk': 'Bukat', 'bvl': 'Bolivian Sign Language', 'bvm': 'Bamunka', 'bvn': 'Buna', 'bvo': 'Bolgo', 'bvp': 'Bumang', 'bvq': 'Birri', 'bvr': 'Burarra', 'bvt': 'Bati (Indonesia)', 'bvu': 'Bukit Malay', 'bvv': 'Baniva', 'bvw': 'Boga', 'bvx': 'Dibole', 'bvy': 'Baybayanon', 'bvz': 'Bauzi', 'bwa': 'Bwatoo', 'bwb': 'Namosi-Naitasiri-Serua', 'bwc': 'Bwile', 'bwd': 'Bwaidoka', 'bwe': 'Bwe Karen', 'bwf': 'Boselewa', 'bwg': 'Barwe', 'bwh': 'Bishuo', 'bwi': 'Baniwa', 'bwj': 'Láá Láá Bwamu', 'bwk': 'Bauwaki', 'bwl': 'Bwela', 'bwm': 'Biwat', 'bwn': 'Wunai Bunu', 'bwo': 'Boro (Ethiopia)', 'bwp': 'Mandobo Bawah', 'bwq': 'Southern Bobo Madaré', 'bwr': 'Bura-Pabir', 'bws': 'Bomboma', 'bwt': 'Bafaw-Balong', 'bwu': 'Buli (Ghana)', 'bww': 'Bwa', 'bwx': 'Bu-Nao Bunu', 'bwy': 'Cwi Bwamu', 'bwz': 'Bwisi', 'bxa': 'Tairaha', 'bxb': 'Belanda Bor', 'bxc': 'Molengue', 'bxd': 'Pela', 'bxe': 'Birale', 'bxf': 'Bilur', 'bxg': 'Bangala', 'bxh': 'Buhutu', 'bxi': 'Pirlatapa', 'bxj': 'Bayungu', 'bxk': 'Bukusu', 'bxl': 'Jalkunan', 'bxm': 'Mongolia Buriat', 'bxn': 'Burduna', 'bxo': 'Barikanchi', 'bxp': 'Bebil', 'bxq': 'Beele', 'bxr': 'Russia Buriat', 'bxs': 'Busam', 'bxu': 'China Buriat', 'bxv': 'Berakou', 'bxw': 'Bankagooma', 'bxz': 'Binahari', 'bya': 'Batak', 'byb': 'Bikya', 'byc': 'Ubaghara', 'byd': "Benyadu'", 'bye': 'Pouye', 'byf': 'Bete', 'byg': 'Baygo', 'byh': 'Bhujel', 'byi': 'Buyu', 'byj': 'Bina (Nigeria)', 'byk': 'Biao', 'byl': 'Bayono', 'bym': 'Bidyara', 'byn': 'Bilin', 'byo': 'Biyo', 'byp': 'Bumaji', 'byq': 'Basay', 'byr': 'Baruya', 'bys': 'Burak', 'byt': 'Berti', 'byv': 'Medumba', 'byw': 'Belhariya', 'byx': 'Qaqet', 'byz': 'Banaro', 'bza': 'Bandi', 'bzb': 'Andio', 'bzc': 'Southern Betsimisaraka Malagasy', 'bzd': 'Bribri', 'bze': 'Jenaama Bozo', 'bzf': 'Boikin', 'bzg': 'Babuza', 'bzh': 'Mapos Buang', 'bzi': 'Bisu', 'bzj': 'Belize Kriol English', 'bzk': 'Nicaragua Creole English', 'bzl': 'Boano (Sulawesi)', 'bzm': 'Bolondo', 'bzn': 'Boano (Maluku)', 'bzo': 'Bozaba', 'bzp': 'Kemberano', 'bzq': 'Buli (Indonesia)', 'bzr': 'Biri', 'bzs': 'Brazilian Sign Language', 'bzt': 'Brithenig', 'bzu': 'Burmeso', 'bzv': 'Naami', 'bzw': 'Basa (Nigeria)', 'bzx': 'Kɛlɛngaxo Bozo', 'bzy': 'Obanliku', 'bzz': 'Evant', 'caa': 'Chortí', 'cab': 'Garifuna', 'cac': 'Chuj', 'cad': 'Caddo', 'cae': 'Lehar', 'caf': 'Southern Carrier', 'cag': 'Nivaclé', 'cah': 'Cahuarano', 'caj': 'Chané', 'cak': 'Kaqchikel', 'cal': 'Carolinian', 'cam': 'Cemuhî', 'can': 'Chambri', 'cao': 'Chácobo', 'cap': 'Chipaya', 'caq': 'Car Nicobarese', 'car': 'Galibi Carib', 'cas': 'Tsimané', 'cat': 'Catalan', 'cav': 'Cavineña', 'caw': 'Callawalla', 'cax': 'Chiquitano', 'cay': 'Cayuga', 'caz': 'Canichana', 'cbb': 'Cabiyarí', 'cbc': 'Carapana', 'cbd': 'Carijona', 'cbg': 'Chimila', 'cbi': 'Chachi', 'cbj': 'Ede Cabe', 'cbk': 'Chavacano', 'cbl': 'Bualkhaw Chin', 'cbn': 'Nyahkur', 'cbo': 'Izora', 'cbq': 'Tsucuba', 'cbr': 'Cashibo-Cacataibo', 'cbs': 'Cashinahua', 'cbt': 'Chayahuita', 'cbu': 'Candoshi-Shapra', 'cbv': 'Cacua', 'cbw': 'Kinabalian', 'cby': 'Carabayo', 'cca': 'Cauca', 'ccc': 'Chamicuro', 'ccd': 'Cafundo Creole', 'cce': 'Chopi', 'ccg': 'Samba Daka', 'cch': 'Atsam', 'ccj': 'Kasanga', 'ccl': 'Cutchi-Swahili', 'ccm': 'Malaccan Creole Malay', 'cco': 'Comaltepec Chinantec', 'ccp': 'Chakma', 'ccr': 'Cacaopera', 'cda': 'Choni', 'cde': 'Chenchu', 'cdf': 'Chiru', 'cdg': 'Chamari', 'cdh': 'Chambeali', 'cdi': 'Chodri', 'cdj': 'Churahi', 'cdm': 'Chepang', 'cdn': 'Chaudangsi', 'cdo': 'Min Dong Chinese', 'cdr': 'Cinda-Regi-Tiyal', 'cds': 'Chadian Sign Language', 'cdy': 'Chadong', 'cdz': 'Koda', 'cea': 'Lower Chehalis', 'ceb': 'Cebuano', 'ceg': 'Chamacoco', 'cek': 'Eastern Khumi Chin', 'cen': 'Cen', 'ces': 'Czech', 'cet': 'Centúúm', 'cfa': 'Dijim-Bwilim', 'cfd': 'Cara', 'cfg': 'Como Karim', 'cfm': 'Falam Chin', 'cga': 'Changriwa', 'cgc': 'Kagayanen', 'cgg': 'Chiga', 'cgk': 'Chocangacakha', 'cha': 'Chamorro', 'chb': 'Chibcha', 'chc': 'Catawba', 'chd': 'Highland Oaxaca Chontal', 'che': 'Chechen', 'chf': 'Tabasco Chontal', 'chg': 'Chagatai', 'chh': 'Chinook', 'chj': 'Ojitlán Chinantec', 'chk': 'Chuukese', 'chl': 'Cahuilla', 'chm': 'Mari (Russia)', 'chn': 'Chinook jargon', 'cho': 'Choctaw', 'chp': 'Chipewyan', 'chq': 'Quiotepec Chinantec', 'chr': 'Cherokee', 'cht': 'Cholón', 'chu': 'Church Slavic', 'chv': 'Chuvash', 'chw': 'Chuwabu', 'chx': 'Chantyal', 'chy': 'Cheyenne', 'chz': 'Ozumacín Chinantec', 'cia': 'Cia-Cia', 'cib': 'Ci Gbe', 'cic': 'Chickasaw', 'cid': 'Chimariko', 'cie': 'Cineni', 'cih': 'Chinali', 'cik': 'Chitkuli Kinnauri', 'cim': 'Cimbrian', 'cin': 'Cinta Larga', 'cip': 'Chiapanec', 'cir': 'Tiri', 'ciw': 'Chippewa', 'ciy': 'Chaima', 'cja': 'Western Cham', 'cje': 'Chru', 'cjh': 'Upper Chehalis', 'cji': 'Chamalal', 'cjk': 'Chokwe', 'cjm': 'Eastern Cham', 'cjn': 'Chenapian', 'cjo': 'Ashéninka Pajonal', 'cjp': 'Cabécar', 'cjs': 'Shor', 'cjv': 'Chuave', 'cjy': 'Jinyu Chinese', 'ckb': 'Central Kurdish', 'ckh': 'Chak', 'ckl': 'Cibak', 'ckn': 'Kaang Chin', 'cko': 'Anufo', 'ckq': 'Kajakse', 'ckr': 'Kairak', 'cks': 'Tayo', 'ckt': 'Chukot', 'cku': 'Koasati', 'ckv': 'Kavalan', 'ckx': 'Caka', 'cky': 'Cakfem-Mushere', 'ckz': 'Cakchiquel-Quiché Mixed Language', 'cla': 'Ron', 'clc': 'Chilcotin', 'cld': 'Chaldean Neo-Aramaic', 'cle': 'Lealao Chinantec', 'clh': 'Chilisso', 'cli': 'Chakali', 'clj': 'Laitu Chin', 'clk': 'Idu-Mishmi', 'cll': 'Chala', 'clm': 'Clallam', 'clo': 'Lowland Oaxaca Chontal', 'clt': 'Lautu Chin', 'clu': 'Caluyanun', 'clw': 'Chulym', 'cly': 'Eastern Highland Chatino', 'cma': 'Maa', 'cme': 'Cerma', 'cmg': 'Classical Mongolian', 'cmi': 'Emberá-Chamí', 'cml': 'Campalagian', 'cmm': 'Michigamea', 'cmn': 'Mandarin Chinese', 'cmo': 'Central Mnong', 'cmr': 'Mro-Khimi Chin', 'cms': 'Messapic', 'cmt': 'Camtho', 'cna': 'Changthang', 'cnb': 'Chinbon Chin', 'cnc': 'Côông', 'cng': 'Northern Qiang', 'cnh': 'Hakha Chin', 'cni': 'Asháninka', 'cnk': 'Khumi Chin', 'cnl': 'Lalana Chinantec', 'cno': 'Con', 'cns': 'Central Asmat', 'cnt': 'Tepetotutla Chinantec', 'cnu': 'Chenoua', 'cnw': 'Ngawn Chin', 'cnx': 'Middle Cornish', 'coa': 'Cocos Islands Malay', 'cob': 'Chicomuceltec', 'coc': 'Cocopa', 'cod': 'Cocama-Cocamilla', 'coe': 'Koreguaje', 'cof': 'Colorado', 'cog': 'Chong', 'coh': 'Chonyi-Dzihana-Kauma', 'coj': 'Cochimi', 'cok': 'Santa Teresa Cora', 'col': 'Columbia-Wenatchi', 'com': 'Comanche', 'con': 'Cofán', 'coo': 'Comox', 'cop': 'Coptic', 'coq': 'Coquille', 'cor': 'Cornish', 'cos': 'Corsican', 'cot': 'Caquinte', 'cou': 'Wamey', 'cov': 'Cao Miao', 'cow': 'Cowlitz', 'cox': 'Nanti', 'coz': 'Chochotec', 'cpa': 'Palantla Chinantec', 'cpb': 'Ucayali-Yurúa Ashéninka', 'cpc': 'Ajyíninka Apurucayali', 'cpg': 'Cappadocian Greek', 'cpi': 'Chinese Pidgin English', 'cpn': 'Cherepon', 'cpo': 'Kpeego', 'cps': 'Capiznon', 'cpu': 'Pichis Ashéninka', 'cpx': 'Pu-Xian Chinese', 'cpy': 'South Ucayali Ashéninka', 'cqd': 'Chuanqiandian Cluster Miao', 'cra': 'Chara', 'crb': 'Island Carib', 'crc': 'Lonwolwol', 'crd': "Coeur d'Alene", 'cre': 'Cree', 'crf': 'Caramanta', 'crg': 'Michif', 'crh': 'Crimean Tatar', 'cri': 'Sãotomense', 'crj': 'Southern East Cree', 'crk': 'Plains Cree', 'crl': 'Northern East Cree', 'crm': 'Moose Cree', 'crn': 'El Nayar Cora', 'cro': 'Crow', 'crq': "Iyo'wujwa Chorote", 'crr': 'Carolina Algonquian', 'crs': 'Seselwa Creole French', 'crt': "Iyojwa'ja Chorote", 'crv': 'Chaura', 'crw': 'Chrau', 'crx': 'Carrier', 'cry': 'Cori', 'crz': 'Cruzeño', 'csa': 'Chiltepec Chinantec', 'csb': 'Kashubian', 'csc': 'Catalan Sign Language', 'csd': 'Chiangmai Sign Language', 'cse': 'Czech Sign Language', 'csf': 'Cuba Sign Language', 'csg': 'Chilean Sign Language', 'csh': 'Asho Chin', 'csi': 'Coast Miwok', 'csj': 'Songlai Chin', 'csk': 'Jola-Kasa', 'csl': 'Chinese Sign Language', 'csm': 'Central Sierra Miwok', 'csn': 'Colombian Sign Language', 'cso': 'Sochiapam Chinantec', 'csq': 'Croatia Sign Language', 'csr': 'Costa Rican Sign Language', 'css': 'Southern Ohlone', 'cst': 'Northern Ohlone', 'csv': 'Sumtu Chin', 'csw': 'Swampy Cree', 'csy': 'Siyin Chin', 'csz': 'Coos', 'cta': 'Tataltepec Chatino', 'ctc': 'Chetco', 'ctd': 'Tedim Chin', 'cte': 'Tepinapa Chinantec', 'ctg': 'Chittagonian', 'cth': 'Thaiphum Chin', 'ctl': 'Tlacoatzintepec Chinantec', 'ctm': 'Chitimacha', 'ctn': 'Chhintange', 'cto': 'Emberá-Catío', 'ctp': 'Western Highland Chatino', 'cts': 'Northern Catanduanes Bikol', 'ctt': 'Wayanad Chetti', 'ctu': 'Chol', 'ctz': 'Zacatepec Chatino', 'cua': 'Cua', 'cub': 'Cubeo', 'cuc': 'Usila Chinantec', 'cug': 'Cung', 'cuh': 'Chuka', 'cui': 'Cuiba', 'cuj': 'Mashco Piro', 'cuk': 'San Blas Kuna', 'cul': 'Culina', 'cuo': 'Cumanagoto', 'cup': 'Cupeño', 'cuq': 'Cun', 'cur': 'Chhulung', 'cut': 'Teutila Cuicatec', 'cuu': 'Tai Ya', 'cuv': 'Cuvok', 'cuw': 'Chukwa', 'cux': 'Tepeuxila Cuicatec', 'cvg': 'Chug', 'cvn': 'Valle Nacional Chinantec', 'cwa': 'Kabwa', 'cwb': 'Maindo', 'cwd': 'Woods Cree', 'cwe': 'Kwere', 'cwg': 'Chewong', 'cwt': 'Kuwaataay', 'cya': 'Nopala Chatino', 'cyb': 'Cayubaba', 'cym': 'Welsh', 'cyo': 'Cuyonon', 'czh': 'Huizhou Chinese', 'czk': 'Knaanic', 'czn': 'Zenzontepec Chatino', 'czo': 'Min Zhong Chinese', 'czt': 'Zotung Chin', 'daa': 'Dangaléat', 'dac': 'Dambi', 'dad': 'Marik', 'dae': 'Duupa', 'dag': 'Dagbani', 'dah': 'Gwahatike', 'dai': 'Day', 'daj': 'Dar Fur Daju', 'dak': 'Dakota', 'dal': 'Dahalo', 'dam': 'Damakawa', 'dan': 'Danish', 'dao': 'Daai Chin', 'daq': 'Dandami Maria', 'dar': 'Dargwa', 'das': 'Daho-Doo', 'dau': 'Dar Sila Daju', 'dav': 'Taita', 'daw': 'Davawenyo', 'dax': 'Dayi', 'daz': 'Dao', 'dba': 'Bangime', 'dbb': 'Deno', 'dbd': 'Dadiya', 'dbe': 'Dabe', 'dbf': 'Edopi', 'dbg': 'Dogul Dom Dogon', 'dbi': 'Doka', 'dbj': "Ida'an", 'dbl': 'Dyirbal', 'dbm': 'Duguri', 'dbn': 'Duriankere', 'dbo': 'Dulbu', 'dbp': 'Duwai', 'dbq': 'Daba', 'dbr': 'Dabarre', 'dbt': 'Ben Tey Dogon', 'dbu': 'Bondum Dom Dogon', 'dbv': 'Dungu', 'dbw': 'Bankan Tey Dogon', 'dby': 'Dibiyaso', 'dcc': 'Deccan', 'dcr': 'Negerhollands', 'dda': 'Dadi Dadi', 'ddd': 'Dongotono', 'dde': 'Doondo', 'ddg': 'Fataluku', 'ddi': 'West Goodenough', 'ddj': 'Jaru', 'ddn': 'Dendi (Benin)', 'ddo': 'Dido', 'ddr': 'Dhudhuroa', 'dds': 'Donno So Dogon', 'ddw': 'Dawera-Daweloor', 'dec': 'Dagik', 'ded': 'Dedua', 'dee': 'Dewoin', 'def': 'Dezfuli', 'deg': 'Degema', 'deh': 'Dehwari', 'dei': 'Demisa', 'dek': 'Dek', 'del': 'Delaware', 'dem': 'Dem', 'den': 'Slave (Athapascan)', 'dep': 'Pidgin Delaware', 'deq': 'Dendi (Central African Republic)', 'der': 'Deori', 'des': 'Desano', 'deu': 'German', 'dev': 'Domung', 'dez': 'Dengese', 'dga': 'Southern Dagaare', 'dgb': 'Bunoge Dogon', 'dgc': 'Casiguran Dumagat Agta', 'dgd': 'Dagaari Dioula', 'dge': 'Degenan', 'dgg': 'Doga', 'dgh': 'Dghwede', 'dgi': 'Northern Dagara', 'dgk': 'Dagba', 'dgl': 'Andaandi', 'dgn': 'Dagoman', 'dgo': 'Dogri (individual language)', 'dgr': 'Dogrib', 'dgs': 'Dogoso', 'dgt': "Ndra'ngith", 'dgu': 'Degaru', 'dgw': 'Daungwurrung', 'dgx': 'Doghoro', 'dgz': 'Daga', 'dhd': 'Dhundari', 'dhg': 'Dhangu-Djangu', 'dhi': 'Dhimal', 'dhl': 'Dhalandji', 'dhm': 'Zemba', 'dhn': 'Dhanki', 'dho': 'Dhodia', 'dhr': 'Dhargari', 'dhs': 'Dhaiso', 'dhu': 'Dhurga', 'dhv': 'Dehu', 'dhw': 'Dhanwar (Nepal)', 'dhx': 'Dhungaloo', 'dia': 'Dia', 'dib': 'South Central Dinka', 'dic': 'Lakota Dida', 'did': 'Didinga', 'dif': 'Dieri', 'dig': 'Digo', 'dih': 'Kumiai', 'dii': 'Dimbong', 'dij': 'Dai', 'dik': 'Southwestern Dinka', 'dil': 'Dilling', 'dim': 'Dime', 'din': 'Dinka', 'dio': 'Dibo', 'dip': 'Northeastern Dinka', 'diq': 'Dimli (individual language)', 'dir': 'Dirim', 'dis': 'Dimasa', 'dit': 'Dirari', 'diu': 'Diriku', 'div': 'Dhivehi', 'diw': 'Northwestern Dinka', 'dix': 'Dixon Reef', 'diy': 'Diuwe', 'diz': 'Ding', 'dja': 'Djadjawurrung', 'djb': 'Djinba', 'djc': 'Dar Daju Daju', 'djd': 'Djamindjung', 'dje': 'Zarma', 'djf': 'Djangun', 'dji': 'Djinang', 'djj': 'Djeebbana', 'djk': 'Eastern Maroon Creole', 'djm': 'Jamsay Dogon', 'djn': 'Djauan', 'djo': 'Jangkang', 'djr': 'Djambarrpuyngu', 'dju': 'Kapriman', 'djw': 'Djawi', 'dka': 'Dakpakha', 'dkk': 'Dakka', 'dkr': 'Kuijau', 'dks': 'Southeastern Dinka', 'dkx': 'Mazagway', 'dlg': 'Dolgan', 'dlk': 'Dahalik', 'dlm': 'Dalmatian', 'dln': 'Darlong', 'dma': 'Duma', 'dmb': 'Mombo Dogon', 'dmc': 'Gavak', 'dmd': 'Madhi Madhi', 'dme': 'Dugwor', 'dmg': 'Upper Kinabatangan', 'dmk': 'Domaaki', 'dml': 'Dameli', 'dmm': 'Dama', 'dmo': 'Kemedzung', 'dmr': 'East Damar', 'dms': 'Dampelas', 'dmu': 'Dubu', 'dmv': 'Dumpas', 'dmw': 'Mudburra', 'dmx': 'Dema', 'dmy': 'Demta', 'dna': 'Upper Grand Valley Dani', 'dnd': 'Daonda', 'dne': 'Ndendeule', 'dng': 'Dungan', 'dni': 'Lower Grand Valley Dani', 'dnj': 'Dan', 'dnk': 'Dengka', 'dnn': 'Dzùùngoo', 'dnr': 'Danaru', 'dnt': 'Mid Grand Valley Dani', 'dnu': 'Danau', 'dnv': 'Danu', 'dnw': 'Western Dani', 'dny': 'Dení', 'doa': 'Dom', 'dob': 'Dobu', 'doc': 'Northern Dong', 'doe': 'Doe', 'dof': 'Domu', 'doh': 'Dong', 'doi': 'Dogri (macrolanguage)', 'dok': 'Dondo', 'dol': 'Doso', 'don': 'Toura (Papua New Guinea)', 'doo': 'Dongo', 'dop': 'Lukpa', 'doq': 'Dominican Sign Language', 'dor': "Dori'o", 'dos': 'Dogosé', 'dot': 'Dass', 'dov': 'Dombe', 'dow': 'Doyayo', 'dox': 'Bussa', 'doy': 'Dompo', 'doz': 'Dorze', 'dpp': 'Papar', 'drb': 'Dair', 'drc': 'Minderico', 'drd': 'Darmiya', 'dre': 'Dolpo', 'drg': 'Rungus', 'dri': "C'lela", 'drl': 'Paakantyi', 'drn': 'West Damar', 'dro': 'Daro-Matu Melanau', 'drq': 'Dura', 'drr': 'Dororo', 'drs': 'Gedeo', 'drt': 'Drents', 'dru': 'Rukai', 'dry': 'Darai', 'dsb': 'Lower Sorbian', 'dse': 'Dutch Sign Language', 'dsh': 'Daasanach', 'dsi': 'Disa', 'dsl': 'Danish Sign Language', 'dsn': 'Dusner', 'dso': 'Desiya', 'dsq': 'Tadaksahak', 'dta': 'Daur', 'dtb': 'Labuk-Kinabatangan Kadazan', 'dtd': 'Ditidaht', 'dth': 'Adithinngithigh', 'dti': 'Ana Tinga Dogon', 'dtk': 'Tene Kan Dogon', 'dtm': 'Tomo Kan Dogon', 'dtn': 'Daatsʼíin', 'dto': 'Tommo So Dogon', 'dtp': 'Kadazan Dusun', 'dtr': 'Lotud', 'dts': 'Toro So Dogon', 'dtt': 'Toro Tegu Dogon', 'dtu': 'Tebul Ure Dogon', 'dty': 'Dotyali', 'dua': 'Duala', 'dub': 'Dubli', 'duc': 'Duna', 'dud': 'Hun-Saare', 'due': 'Umiray Dumaget Agta', 'duf': 'Dumbea', 'dug': 'Duruma', 'duh': 'Dungra Bhil', 'dui': 'Dumun', 'duk': 'Uyajitaya', 'dul': 'Alabat Island Agta', 'dum': 'Middle Dutch (ca. 1050-1350)', 'dun': 'Dusun Deyah', 'duo': 'Dupaninan Agta', 'dup': 'Duano', 'duq': 'Dusun Malang', 'dur': 'Dii', 'dus': 'Dumi', 'duu': 'Drung', 'duv': 'Duvle', 'duw': 'Dusun Witu', 'dux': 'Duungooma', 'duy': 'Dicamay Agta', 'duz': 'Duli-Gey', 'dva': 'Duau', 'dwa': 'Diri', 'dwr': 'Dawro', 'dws': 'Dutton World Speedwords', 'dwu': 'Dhuwal', 'dww': 'Dawawa', 'dwy': 'Dhuwaya', 'dya': 'Dyan', 'dyb': 'Dyaberdyaber', 'dyd': 'Dyugun', 'dyg': 'Villa Viciosa Agta', 'dyi': 'Djimini Senoufo', 'dym': 'Yanda Dom Dogon', 'dyn': 'Dyangadi', 'dyo': 'Jola-Fonyi', 'dyu': 'Dyula', 'dyy': 'Dyaabugay', 'dza': 'Tunzu', 'dze': 'Djiwarli', 'dzg': 'Dazaga', 'dzl': 'Dzalakha', 'dzn': 'Dzando', 'dzo': 'Dzongkha', 'eaa': 'Karenggapa', 'ebg': 'Ebughu', 'ebk': 'Eastern Bontok', 'ebo': 'Teke-Ebo', 'ebr': 'Ebrié', 'ebu': 'Embu', 'ecr': 'Eteocretan', 'ecs': 'Ecuadorian Sign Language', 'ecy': 'Eteocypriot', 'eee': 'E', 'efa': 'Efai', 'efe': 'Efe', 'efi': 'Efik', 'ega': 'Ega', 'egl': 'Emilian', 'ego': 'Eggon', 'egy': 'Egyptian (Ancient)', 'ehu': 'Ehueun', 'eip': 'Eipomek', 'eit': 'Eitiep', 'eiv': 'Askopan', 'eja': 'Ejamat', 'eka': 'Ekajuk', 'ekc': 'Eastern Karnic', 'eke': 'Ekit', 'ekg': 'Ekari', 'eki': 'Eki', 'ekk': 'Standard Estonian', 'ekl': 'Kol (Bangladesh)', 'ekm': 'Elip', 'eko': 'Koti', 'ekp': 'Ekpeye', 'ekr': 'Yace', 'eky': 'Eastern Kayah', 'ele': 'Elepi', 'elh': 'El Hugeirat', 'eli': 'Nding', 'elk': 'Elkei', 'ell': 'Modern Greek (1453-)', 'elm': 'Eleme', 'elo': 'El Molo', 'elu': 'Elu', 'elx': 'Elamite', 'ema': 'Emai-Iuleha-Ora', 'emb': 'Embaloh', 'eme': 'Emerillon', 'emg': 'Eastern Meohang', 'emi': 'Mussau-Emira', 'emk': 'Eastern Maninkakan', 'emm': 'Mamulique', 'emn': 'Eman', 'emp': 'Northern Emberá', 'ems': 'Pacific Gulf Yupik', 'emu': 'Eastern Muria', 'emw': 'Emplawas', 'emx': 'Erromintxela', 'emy': 'Epigraphic Mayan', 'ena': 'Apali', 'enb': 'Markweeta', 'enc': 'En', 'end': 'Ende', 'enf': 'Forest Enets', 'eng': 'English', 'enh': 'Tundra Enets', 'enl': 'Enlhet', 'enm': 'Middle English (1100-1500)', 'enn': 'Engenni', 'eno': 'Enggano', 'enq': 'Enga', 'enr': 'Emumu', 'enu': 'Enu', 'env': 'Enwan (Edu State)', 'enw': 'Enwan (Akwa Ibom State)', 'enx': 'Enxet', 'eot': "Beti (Côte d'Ivoire)", 'epi': 'Epie', 'epo': 'Esperanto', 'era': 'Eravallan', 'erg': 'Sie', 'erh': 'Eruwa', 'eri': 'Ogea', 'erk': 'South Efate', 'ero': 'Horpa', 'err': 'Erre', 'ers': 'Ersu', 'ert': 'Eritai', 'erw': 'Erokwanas', 'ese': 'Ese Ejja', 'esg': 'Aheri Gondi', 'esh': 'Eshtehardi', 'esi': 'North Alaskan Inupiatun', 'esk': 'Northwest Alaska Inupiatun', 'esl': 'Egypt Sign Language', 'esm': 'Esuma', 'esn': 'Salvadoran Sign Language', 'eso': 'Estonian Sign Language', 'esq': 'Esselen', 'ess': 'Central Siberian Yupik', 'est': 'Estonian', 'esu': 'Central Yupik', 'esy': 'Eskayan', 'etb': 'Etebi', 'etc': 'Etchemin', 'eth': 'Ethiopian Sign Language', 'etn': 'Eton (Vanuatu)', 'eto': 'Eton (Cameroon)', 'etr': 'Edolo', 'ets': 'Yekhee', 'ett': 'Etruscan', 'etu': 'Ejagham', 'etx': 'Eten', 'etz': 'Semimi', 'eus': 'Basque', 'eve': 'Even', 'evh': 'Uvbie', 'evn': 'Evenki', 'ewe': 'Ewe', 'ewo': 'Ewondo', 'ext': 'Extremaduran', 'eya': 'Eyak', 'eyo': 'Keiyo', 'eza': 'Ezaa', 'eze': 'Uzekwe', 'faa': 'Fasu', 'fab': "Fa d'Ambu", 'fad': 'Wagi', 'faf': 'Fagani', 'fag': 'Finongan', 'fah': 'Baissa Fali', 'fai': 'Faiwol', 'faj': 'Faita', 'fak': 'Fang (Cameroon)', 'fal': 'South Fali', 'fam': 'Fam', 'fan': 'Fang (Equatorial Guinea)', 'fao': 'Faroese', 'fap': 'Palor', 'far': 'Fataleka', 'fas': 'Persian', 'fat': 'Fanti', 'fau': 'Fayu', 'fax': 'Fala', 'fay': 'Southwestern Fars', 'faz': 'Northwestern Fars', 'fbl': 'West Albay Bikol', 'fcs': 'Quebec Sign Language', 'fer': 'Feroge', 'ffi': 'Foia Foia', 'ffm': 'Maasina Fulfulde', 'fgr': 'Fongoro', 'fia': 'Nobiin', 'fie': 'Fyer', 'fij': 'Fijian', 'fil': 'Filipino', 'fin': 'Finnish', 'fip': 'Fipa', 'fir': 'Firan', 'fit': 'Tornedalen Finnish', 'fiw': 'Fiwaga', 'fkk': 'Kirya-Konzəl', 'fkv': 'Kven Finnish', 'fla': "Kalispel-Pend d'Oreille", 'flh': 'Foau', 'fli': 'Fali', 'fll': 'North Fali', 'fln': 'Flinders Island', 'flr': 'Fuliiru', 'fly': 'Flaaitaal', 'fmp': "Fe'fe'", 'fmu': 'Far Western Muria', 'fnb': 'Fanbak', 'fng': 'Fanagalo', 'fni': 'Fania', 'fod': 'Foodo', 'foi': 'Foi', 'fom': 'Foma', 'fon': 'Fon', 'for': 'Fore', 'fos': 'Siraya', 'fpe': 'Fernando Po Creole English', 'fqs': 'Fas', 'fra': 'French', 'frc': 'Cajun French', 'frd': 'Fordata', 'frk': 'Frankish', 'frm': 'Middle French (ca. 1400-1600)', 'fro': 'Old French (842-ca. 1400)', 'frp': 'Arpitan', 'frq': 'Forak', 'frr': 'Northern Frisian', 'frs': 'Eastern Frisian', 'frt': 'Fortsenal', 'fry': 'Western Frisian', 'fse': 'Finnish Sign Language', 'fsl': 'French Sign Language', 'fss': 'Finland-Swedish Sign Language', 'fub': 'Adamawa Fulfulde', 'fuc': 'Pulaar', 'fud': 'East Futuna', 'fue': 'Borgu Fulfulde', 'fuf': 'Pular', 'fuh': 'Western Niger Fulfulde', 'fui': 'Bagirmi Fulfulde', 'fuj': 'Ko', 'ful': 'Fulah', 'fum': 'Fum', 'fun': 'Fulniô', 'fuq': 'Central-Eastern Niger Fulfulde', 'fur': 'Friulian', 'fut': 'Futuna-Aniwa', 'fuu': 'Furu', 'fuv': 'Nigerian Fulfulde', 'fuy': 'Fuyug', 'fvr': 'Fur', 'fwa': 'Fwâi', 'fwe': 'Fwe', 'gaa': 'Ga', 'gab': 'Gabri', 'gac': 'Mixed Great Andamanese', 'gad': 'Gaddang', 'gae': 'Guarequena', 'gaf': 'Gende', 'gag': 'Gagauz', 'gah': 'Alekano', 'gai': 'Borei', 'gaj': 'Gadsup', 'gak': 'Gamkonora', 'gal': 'Galolen', 'gam': 'Kandawo', 'gan': 'Gan Chinese', 'gao': 'Gants', 'gap': 'Gal', 'gaq': "Gata'", 'gar': 'Galeya', 'gas': 'Adiwasi Garasia', 'gat': 'Kenati', 'gau': 'Mudhili Gadaba', 'gaw': 'Nobonob', 'gax': 'Borana-Arsi-Guji Oromo', 'gay': 'Gayo', 'gaz': 'West Central Oromo', 'gba': 'Gbaya (Central African Republic)', 'gbb': 'Kaytetye', 'gbd': 'Karadjeri', 'gbe': 'Niksek', 'gbf': 'Gaikundi', 'gbg': 'Gbanziri', 'gbh': 'Defi Gbe', 'gbi': 'Galela', 'gbj': 'Bodo Gadaba', 'gbk': 'Gaddi', 'gbl': 'Gamit', 'gbm': 'Garhwali', 'gbn': "Mo'da", 'gbo': 'Northern Grebo', 'gbp': 'Gbaya-Bossangoa', 'gbq': 'Gbaya-Bozoum', 'gbr': 'Gbagyi', 'gbs': 'Gbesi Gbe', 'gbu': 'Gagadu', 'gbv': 'Gbanu', 'gbw': 'Gabi-Gabi', 'gbx': 'Eastern Xwla Gbe', 'gby': 'Gbari', 'gbz': 'Zoroastrian Dari', 'gcc': 'Mali', 'gcd': 'Ganggalida', 'gce': 'Galice', 'gcf': 'Guadeloupean Creole French', 'gcl': 'Grenadian Creole English', 'gcn': 'Gaina', 'gcr': 'Guianese Creole French', 'gct': 'Colonia Tovar German', 'gda': 'Gade Lohar', 'gdb': 'Pottangi Ollar Gadaba', 'gdc': 'Gugu Badhun', 'gdd': 'Gedaged', 'gde': 'Gude', 'gdf': 'Guduf-Gava', 'gdg': "Ga'dang", 'gdh': 'Gadjerawang', 'gdi': 'Gundi', 'gdj': 'Gurdjar', 'gdk': 'Gadang', 'gdl': 'Dirasha', 'gdm': 'Laal', 'gdn': 'Umanakaina', 'gdo': 'Ghodoberi', 'gdq': 'Mehri', 'gdr': 'Wipi', 'gds': 'Ghandruk Sign Language', 'gdt': 'Kungardutyi', 'gdu': 'Gudu', 'gdx': 'Godwari', 'gea': 'Geruma', 'geb': 'Kire', 'gec': 'Gboloo Grebo', 'ged': 'Gade', 'geg': 'Gengle', 'geh': 'Hutterite German', 'gei': 'Gebe', 'gej': 'Gen', 'gek': 'Ywom', 'gel': "ut-Ma'in", 'geq': 'Geme', 'ges': 'Geser-Gorom', 'gev': 'Eviya', 'gew': 'Gera', 'gex': 'Garre', 'gey': 'Enya', 'gez': 'Geez', 'gfk': 'Patpatar', 'gft': 'Gafat', 'gga': 'Gao', 'ggb': 'Gbii', 'ggd': 'Gugadj', 'gge': 'Guragone', 'ggg': 'Gurgula', 'ggk': 'Kungarakany', 'ggl': 'Ganglau', 'ggt': 'Gitua', 'ggu': 'Gagu', 'ggw': 'Gogodala', 'gha': 'Ghadamès', 'ghc': 'Hiberno-Scottish Gaelic', 'ghe': 'Southern Ghale', 'ghh': 'Northern Ghale', 'ghk': 'Geko Karen', 'ghl': 'Ghulfan', 'ghn': 'Ghanongga', 'gho': 'Ghomara', 'ghr': 'Ghera', 'ghs': 'Guhu-Samane', 'ght': 'Kuke', 'gia': 'Kitja', 'gib': 'Gibanawa', 'gic': 'Gail', 'gid': 'Gidar', 'gig': 'Goaria', 'gih': 'Githabul', 'gil': 'Gilbertese', 'gim': 'Gimi (Eastern Highlands)', 'gin': 'Hinukh', 'gip': 'Gimi (West New Britain)', 'giq': 'Green Gelao', 'gir': 'Red Gelao', 'gis': 'North Giziga', 'git': 'Gitxsan', 'giu': 'Mulao', 'giw': 'White Gelao', 'gix': 'Gilima', 'giy': 'Giyug', 'giz': 'South Giziga', 'gji': 'Geji', 'gjk': 'Kachi Koli', 'gjm': 'Gunditjmara', 'gjn': 'Gonja', 'gjr': 'Gurindji Kriol', 'gju': 'Gujari', 'gka': 'Guya', 'gke': 'Ndai', 'gkn': 'Gokana', 'gko': 'Kok-Nar', 'gkp': 'Guinea Kpelle', 'gku': 'ǂUngkue', 'gla': 'Scottish Gaelic', 'glc': 'Bon Gula', 'gld': 'Nanai', 'gle': 'Irish', 'glg': 'Galician', 'glh': 'Northwest Pashai', 'gli': 'Guliguli', 'glj': 'Gula Iro', 'glk': 'Gilaki', 'gll': 'Garlali', 'glo': 'Galambu', 'glr': 'Glaro-Twabo', 'glu': 'Gula (Chad)', 'glv': 'Manx', 'glw': 'Glavda', 'gly': 'Gule', 'gma': 'Gambera', 'gmb': "Gula'alaa", 'gmd': 'Mághdì', 'gmg': 'Magɨyi', 'gmh': 'Middle High German (ca. 1050-1500)', 'gml': 'Middle Low German', 'gmm': 'Gbaya-Mbodomo', 'gmn': 'Gimnime', 'gmu': 'Gumalu', 'gmv': 'Gamo', 'gmx': 'Magoma', 'gmy': 'Mycenaean Greek', 'gmz': 'Mgbolizhia', 'gna': 'Kaansa', 'gnb': 'Gangte', 'gnc': 'Guanche', 'gnd': 'Zulgo-Gemzek', 'gne': 'Ganang', 'gng': 'Ngangam', 'gnh': 'Lere', 'gni': 'Gooniyandi', 'gnk': '//Gana', 'gnl': 'Gangulu', 'gnm': 'Ginuman', 'gnn': 'Gumatj', 'gno': 'Northern Gondi', 'gnq': 'Gana', 'gnr': 'Gureng Gureng', 'gnt': 'Guntai', 'gnu': 'Gnau', 'gnw': 'Western Bolivian Guaraní', 'gnz': 'Ganzi', 'goa': 'Guro', 'gob': 'Playero', 'goc': 'Gorakor', 'god': 'Godié', 'goe': 'Gongduk', 'gof': 'Gofa', 'gog': 'Gogo', 'goh': 'Old High German (ca. 750-1050)', 'goi': 'Gobasi', 'goj': 'Gowlan', 'gok': 'Gowli', 'gol': 'Gola', 'gom': 'Goan Konkani', 'gon': 'Gondi', 'goo': 'Gone Dau', 'gop': 'Yeretuar', 'goq': 'Gorap', 'gor': 'Gorontalo', 'gos': 'Gronings', 'got': 'Gothic', 'gou': 'Gavar', 'gow': 'Gorowa', 'gox': 'Gobu', 'goy': 'Goundo', 'goz': 'Gozarkhani', 'gpa': 'Gupa-Abawa', 'gpe': 'Ghanaian Pidgin English', 'gpn': 'Taiap', 'gqa': "Ga'anda", 'gqi': 'Guiqiong', 'gqn': 'Guana (Brazil)', 'gqr': 'Gor', 'gqu': 'Qau', 'gra': 'Rajput Garasia', 'grb': 'Grebo', 'grc': 'Ancient Greek (to 1453)', 'grd': 'Guruntum-Mbaaru', 'grg': 'Madi', 'grh': 'Gbiri-Niragu', 'gri': 'Ghari', 'grj': 'Southern Grebo', 'grm': 'Kota Marudu Talantang', 'grn': 'Guarani', 'gro': 'Groma', 'grq': 'Gorovu', 'grr': 'Taznatit', 'grs': 'Gresi', 'grt': 'Garo', 'gru': 'Kistane', 'grv': 'Central Grebo', 'grw': 'Gweda', 'grx': 'Guriaso', 'gry': 'Barclayville Grebo', 'grz': 'Guramalum', 'gse': 'Ghanaian Sign Language', 'gsg': 'German Sign Language', 'gsl': 'Gusilay', 'gsm': 'Guatemalan Sign Language', 'gsn': 'Nema', 'gso': 'Southwest Gbaya', 'gsp': 'Wasembo', 'gss': 'Greek Sign Language', 'gsw': 'Swiss German', 'gta': 'Guató', 'gtu': 'Aghu-Tharnggala', 'gua': 'Shiki', 'gub': 'Guajajára', 'guc': 'Wayuu', 'gud': 'Yocoboué Dida', 'gue': 'Gurinji', 'guf': 'Gupapuyngu', 'gug': 'Paraguayan Guaraní', 'guh': 'Guahibo', 'gui': 'Eastern Bolivian Guaraní', 'guj': 'Gujarati', 'guk': 'Gumuz', 'gul': 'Sea Island Creole English', 'gum': 'Guambiano', 'gun': 'Mbyá Guaraní', 'guo': 'Guayabero', 'gup': 'Gunwinggu', 'guq': 'Aché', 'gur': 'Farefare', 'gus': 'Guinean Sign Language', 'gut': 'Maléku Jaíka', 'guu': 'Yanomamö', 'guw': 'Gun', 'gux': 'Gourmanchéma', 'guz': 'Gusii', 'gva': 'Guana (Paraguay)', 'gvc': 'Guanano', 'gve': 'Duwet', 'gvf': 'Golin', 'gvj': 'Guajá', 'gvl': 'Gulay', 'gvm': 'Gurmana', 'gvn': 'Kuku-Yalanji', 'gvo': 'Gavião Do Jiparaná', 'gvp': 'Pará Gavião', 'gvr': 'Gurung', 'gvs': 'Gumawana', 'gvy': 'Guyani', 'gwa': 'Mbato', 'gwb': 'Gwa', 'gwc': 'Kalami', 'gwd': 'Gawwada', 'gwe': 'Gweno', 'gwf': 'Gowro', 'gwg': 'Moo', 'gwi': 'Gwichʼin', 'gwj': '/Gwi', 'gwm': 'Awngthim', 'gwn': 'Gwandara', 'gwr': 'Gwere', 'gwt': 'Gawar-Bati', 'gwu': 'Guwamu', 'gww': 'Kwini', 'gwx': 'Gua', 'gxx': 'Wè Southern', 'gya': 'Northwest Gbaya', 'gyb': 'Garus', 'gyd': 'Kayardild', 'gye': 'Gyem', 'gyf': 'Gungabula', 'gyg': 'Gbayi', 'gyi': 'Gyele', 'gyl': 'Gayil', 'gym': 'Ngäbere', 'gyn': 'Guyanese Creole English', 'gyr': 'Guarayu', 'gyy': 'Gunya', 'gza': 'Ganza', 'gzi': 'Gazi', 'gzn': 'Gane', 'haa': 'Han', 'hab': 'Hanoi Sign Language', 'hac': 'Gurani', 'had': 'Hatam', 'hae': 'Eastern Oromo', 'haf': 'Haiphong Sign Language', 'hag': 'Hanga', 'hah': 'Hahon', 'hai': 'Haida', 'haj': 'Hajong', 'hak': 'Hakka Chinese', 'hal': 'Halang', 'ham': 'Hewa', 'han': 'Hangaza', 'hao': 'Hakö', 'hap': 'Hupla', 'haq': 'Ha', 'har': 'Harari', 'has': 'Haisla', 'hat': 'Haitian', 'hau': 'Hausa', 'hav': 'Havu', 'haw': 'Hawaiian', 'hax': 'Southern Haida', 'hay': 'Haya', 'haz': 'Hazaragi', 'hba': 'Hamba', 'hbb': 'Huba', 'hbn': 'Heiban', 'hbo': 'Ancient Hebrew', 'hbs': 'Serbo-Croatian', 'hbu': 'Habu', 'hca': 'Andaman Creole Hindi', 'hch': 'Huichol', 'hdn': 'Northern Haida', 'hds': 'Honduras Sign Language', 'hdy': 'Hadiyya', 'hea': 'Northern Qiandong Miao', 'heb': 'Hebrew', 'hed': 'Herdé', 'heg': 'Helong', 'heh': 'Hehe', 'hei': 'Heiltsuk', 'hem': 'Hemba', 'her': 'Herero', 'hgm': 'Hai//om', 'hgw': 'Haigwai', 'hhi': 'Hoia Hoia', 'hhr': 'Kerak', 'hhy': 'Hoyahoya', 'hia': 'Lamang', 'hib': 'Hibito', 'hid': 'Hidatsa', 'hif': 'Fiji Hindi', 'hig': 'Kamwe', 'hih': 'Pamosu', 'hii': 'Hinduri', 'hij': 'Hijuk', 'hik': 'Seit-Kaitetu', 'hil': 'Hiligaynon', 'hin': 'Hindi', 'hio': 'Tsoa', 'hir': 'Himarimã', 'hit': 'Hittite', 'hiw': 'Hiw', 'hix': 'Hixkaryána', 'hji': 'Haji', 'hka': 'Kahe', 'hke': 'Hunde', 'hkk': 'Hunjara-Kaina Ke', 'hks': 'Hong Kong Sign Language', 'hla': 'Halia', 'hlb': 'Halbi', 'hld': 'Halang Doan', 'hle': 'Hlersu', 'hlt': 'Matu Chin', 'hlu': 'Hieroglyphic Luwian', 'hma': 'Southern Mashan Hmong', 'hmb': 'Humburi Senni Songhay', 'hmc': 'Central Huishui Hmong', 'hmd': 'Large Flowery Miao', 'hme': 'Eastern Huishui Hmong', 'hmf': 'Hmong Don', 'hmg': 'Southwestern Guiyang Hmong', 'hmh': 'Southwestern Huishui Hmong', 'hmi': 'Northern Huishui Hmong', 'hmj': 'Ge', 'hmk': 'Maek', 'hml': 'Luopohe Hmong', 'hmm': 'Central Mashan Hmong', 'hmn': 'Hmong', 'hmo': 'Hiri Motu', 'hmp': 'Northern Mashan Hmong', 'hmq': 'Eastern Qiandong Miao', 'hmr': 'Hmar', 'hms': 'Southern Qiandong Miao', 'hmt': 'Hamtai', 'hmu': 'Hamap', 'hmv': 'Hmong Dô', 'hmw': 'Western Mashan Hmong', 'hmy': 'Southern Guiyang Hmong', 'hmz': 'Hmong Shua', 'hna': 'Mina (Cameroon)', 'hnd': 'Southern Hindko', 'hne': 'Chhattisgarhi', 'hnh': '//Ani', 'hni': 'Hani', 'hnj': 'Hmong Njua', 'hnn': 'Hanunoo', 'hno': 'Northern Hindko', 'hns': 'Caribbean Hindustani', 'hnu': 'Hung', 'hoa': 'Hoava', 'hob': 'Mari (Madang Province)', 'hoc': 'Ho', 'hod': 'Holma', 'hoe': 'Horom', 'hoh': 'Hobyót', 'hoi': 'Holikachuk', 'hoj': 'Hadothi', 'hol': 'Holu', 'hom': 'Homa', 'hoo': 'Holoholo', 'hop': 'Hopi', 'hor': 'Horo', 'hos': 'Ho Chi Minh City Sign Language', 'hot': 'Hote', 'hov': 'Hovongan', 'how': 'Honi', 'hoy': 'Holiya', 'hoz': 'Hozo', 'hpo': 'Hpon', 'hps': "Hawai'i Sign Language (HSL)", 'hra': 'Hrangkhol', 'hrc': 'Niwer Mil', 'hre': 'Hre', 'hrk': 'Haruku', 'hrm': 'Horned Miao', 'hro': 'Haroi', 'hrp': 'Nhirrpi', 'hrt': 'Hértevin', 'hru': 'Hruso', 'hrv': 'Croatian', 'hrw': 'Warwar Feni', 'hrx': 'Hunsrik', 'hrz': 'Harzani', 'hsb': 'Upper Sorbian', 'hsh': 'Hungarian Sign Language', 'hsl': 'Hausa Sign Language', 'hsn': 'Xiang Chinese', 'hss': 'Harsusi', 'hti': 'Hoti', 'hto': 'Minica Huitoto', 'hts': 'Hadza', 'htu': 'Hitu', 'htx': 'Middle Hittite', 'hub': 'Huambisa', 'huc': '=/Hua', 'hud': 'Huaulu', 'hue': 'San Francisco Del Mar Huave', 'huf': 'Humene', 'hug': 'Huachipaeri', 'huh': 'Huilliche', 'hui': 'Huli', 'huj': 'Northern Guiyang Hmong', 'huk': 'Hulung', 'hul': 'Hula', 'hum': 'Hungana', 'hun': 'Hungarian', 'huo': 'Hu', 'hup': 'Hupa', 'huq': 'Tsat', 'hur': 'Halkomelem', 'hus': 'Huastec', 'hut': 'Humla', 'huu': 'Murui Huitoto', 'huv': 'San Mateo Del Mar Huave', 'huw': 'Hukumina', 'hux': 'Nüpode Huitoto', 'huy': 'Hulaulá', 'huz': 'Hunzib', 'hvc': 'Haitian Vodoun Culture Language', 'hve': 'San Dionisio Del Mar Huave', 'hvk': 'Haveke', 'hvn': 'Sabu', 'hvv': 'Santa María Del Mar Huave', 'hwa': 'Wané', 'hwc': "Hawai'i Creole English", 'hwo': 'Hwana', 'hya': 'Hya', 'hye': 'Armenian', 'iai': 'Iaai', 'ian': 'Iatmul', 'iar': 'Purari', 'iba': 'Iban', 'ibb': 'Ibibio', 'ibd': 'Iwaidja', 'ibe': 'Akpes', 'ibg': 'Ibanag', 'ibl': 'Ibaloi', 'ibm': 'Agoi', 'ibn': 'Ibino', 'ibo': 'Igbo', 'ibr': 'Ibuoro', 'ibu': 'Ibu', 'iby': 'Ibani', 'ica': 'Ede Ica', 'ich': 'Etkywan', 'icl': 'Icelandic Sign Language', 'icr': 'Islander Creole English', 'ida': 'Idakho-Isukha-Tiriki', 'idb': 'Indo-Portuguese', 'idc': 'Idon', 'idd': 'Ede Idaca', 'ide': 'Idere', 'idi': 'Idi', 'ido': 'Ido', 'idr': 'Indri', 'ids': 'Idesa', 'idt': 'Idaté', 'idu': 'Idoma', 'ifa': 'Amganad Ifugao', 'ifb': 'Batad Ifugao', 'ife': 'Ifè', 'iff': 'Ifo', 'ifk': 'Tuwali Ifugao', 'ifm': 'Teke-Fuumu', 'ifu': 'Mayoyao Ifugao', 'ify': 'Keley-I Kallahan', 'igb': 'Ebira', 'ige': 'Igede', 'igg': 'Igana', 'igl': 'Igala', 'igm': 'Kanggape', 'ign': 'Ignaciano', 'igo': 'Isebe', 'igs': 'Interglossa', 'igw': 'Igwe', 'ihb': 'Iha Based Pidgin', 'ihi': 'Ihievbe', 'ihp': 'Iha', 'ihw': 'Bidhawal', 'iii': 'Sichuan Yi', 'iin': 'Thiin', 'ijc': 'Izon', 'ije': 'Biseni', 'ijj': 'Ede Ije', 'ijn': 'Kalabari', 'ijs': 'Southeast Ijo', 'ike': 'Eastern Canadian Inuktitut', 'iki': 'Iko', 'ikk': 'Ika', 'ikl': 'Ikulu', 'iko': 'Olulumo-Ikom', 'ikp': 'Ikpeshi', 'ikr': 'Ikaranggal', 'iks': 'Inuit Sign Language', 'ikt': 'Inuinnaqtun', 'iku': 'Inuktitut', 'ikv': 'Iku-Gora-Ankwa', 'ikw': 'Ikwere', 'ikx': 'Ik', 'ikz': 'Ikizu', 'ila': 'Ile Ape', 'ilb': 'Ila', 'ile': 'Interlingue', 'ilg': 'Garig-Ilgar', 'ili': 'Ili Turki', 'ilk': 'Ilongot', 'ilm': 'Iranun (Malaysia)', 'ilo': 'Iloko', 'ilp': 'Iranun (Philippines)', 'ils': 'International Sign', 'ilu': "Ili'uun", 'ilv': 'Ilue', 'ima': 'Mala Malasar', 'imi': 'Anamgura', 'iml': 'Miluk', 'imn': 'Imonda', 'imo': 'Imbongu', 'imr': 'Imroing', 'ims': 'Marsian', 'imy': 'Milyan', 'ina': 'Interlingua (International Auxiliary Language Association)', 'inb': 'Inga', 'ind': 'Indonesian', 'ing': "Degexit'an", 'inh': 'Ingush', 'inj': 'Jungle Inga', 'inl': 'Indonesian Sign Language', 'inm': 'Minaean', 'inn': 'Isinai', 'ino': 'Inoke-Yate', 'inp': 'Iñapari', 'ins': 'Indian Sign Language', 'int': 'Intha', 'inz': 'Ineseño', 'ior': 'Inor', 'iou': 'Tuma-Irumu', 'iow': 'Iowa-Oto', 'ipi': 'Ipili', 'ipk': 'Inupiaq', 'ipo': 'Ipiko', 'iqu': 'Iquito', 'iqw': 'Ikwo', 'ire': 'Iresim', 'irh': 'Irarutu', 'iri': 'Irigwe', 'irk': 'Iraqw', 'irn': 'Irántxe', 'irr': 'Ir', 'iru': 'Irula', 'irx': 'Kamberau', 'iry': 'Iraya', 'isa': 'Isabi', 'isc': 'Isconahua', 'isd': 'Isnag', 'ise': 'Italian Sign Language', 'isg': 'Irish Sign Language', 'ish': 'Esan', 'isi': 'Nkem-Nkum', 'isk': 'Ishkashimi', 'isl': 'Icelandic', 'ism': 'Masimasi', 'isn': 'Isanzu', 'iso': 'Isoko', 'isr': 'Israeli Sign Language', 'ist': 'Istriot', 'isu': 'Isu (Menchum Division)', 'ita': 'Italian', 'itb': 'Binongan Itneg', 'itd': 'Southern Tidung', 'ite': 'Itene', 'iti': 'Inlaod Itneg', 'itk': 'Judeo-Italian', 'itl': 'Itelmen', 'itm': 'Itu Mbon Uzo', 'ito': 'Itonama', 'itr': 'Iteri', 'its': 'Isekiri', 'itt': 'Maeng Itneg', 'itv': 'Itawit', 'itw': 'Ito', 'itx': 'Itik', 'ity': 'Moyadan Itneg', 'itz': 'Itzá', 'ium': 'Iu Mien', 'ivb': 'Ibatan', 'ivv': 'Ivatan', 'iwk': 'I-Wak', 'iwm': 'Iwam', 'iwo': 'Iwur', 'iws': 'Sepik Iwam', 'ixc': 'Ixcatec', 'ixl': 'Ixil', 'iya': 'Iyayu', 'iyo': 'Mesaka', 'iyx': 'Yaka (Congo)', 'izh': 'Ingrian', 'izr': 'Izere', 'izz': 'Izii', 'jaa': 'Jamamadí', 'jab': 'Hyam', 'jac': "Popti'", 'jad': 'Jahanka', 'jae': 'Yabem', 'jaf': 'Jara', 'jah': 'Jah Hut', 'jaj': 'Zazao', 'jak': 'Jakun', 'jal': 'Yalahatan', 'jam': 'Jamaican Creole English', 'jan': 'Jandai', 'jao': 'Yanyuwa', 'jaq': 'Yaqay', 'jas': 'New Caledonian Javanese', 'jat': 'Jakati', 'jau': 'Yaur', 'jav': 'Javanese', 'jax': 'Jambi Malay', 'jay': 'Yan-nhangu', 'jaz': 'Jawe', 'jbe': 'Judeo-Berber', 'jbi': 'Badjiri', 'jbj': 'Arandai', 'jbk': 'Barikewa', 'jbn': 'Nafusi', 'jbo': 'Lojban', 'jbr': 'Jofotek-Bromnya', 'jbt': 'Jabutí', 'jbu': 'Jukun Takum', 'jbw': 'Yawijibaya', 'jcs': 'Jamaican Country Sign Language', 'jct': 'Krymchak', 'jda': 'Jad', 'jdg': 'Jadgali', 'jdt': 'Judeo-Tat', 'jeb': 'Jebero', 'jee': 'Jerung', 'jeg': 'Jeng', 'jeh': 'Jeh', 'jei': 'Yei', 'jek': 'Jeri Kuo', 'jel': 'Yelmek', 'jen': 'Dza', 'jer': 'Jere', 'jet': 'Manem', 'jeu': 'Jonkor Bourmataguil', 'jgb': 'Ngbee', 'jge': 'Judeo-Georgian', 'jgk': 'Gwak', 'jgo': 'Ngomba', 'jhi': 'Jehai', 'jhs': 'Jhankot Sign Language', 'jia': 'Jina', 'jib': 'Jibu', 'jic': 'Tol', 'jid': 'Bu', 'jie': 'Jilbe', 'jig': 'Djingili', 'jih': 'sTodsde', 'jii': 'Jiiddu', 'jil': 'Jilim', 'jim': 'Jimi (Cameroon)', 'jio': 'Jiamao', 'jiq': 'Guanyinqiao', 'jit': 'Jita', 'jiu': 'Youle Jinuo', 'jiv': 'Shuar', 'jiy': 'Buyuan Jinuo', 'jje': 'Jejueo', 'jjr': 'Bankal', 'jka': 'Kaera', 'jkm': 'Mobwa Karen', 'jko': 'Kubo', 'jkp': 'Paku Karen', 'jkr': 'Koro (India)', 'jku': 'Labir', 'jle': 'Ngile', 'jls': 'Jamaican Sign Language', 'jma': 'Dima', 'jmb': 'Zumbun', 'jmc': 'Machame', 'jmd': 'Yamdena', 'jmi': 'Jimi (Nigeria)', 'jml': 'Jumli', 'jmn': 'Makuri Naga', 'jmr': 'Kamara', 'jms': 'Mashi (Nigeria)', 'jmw': 'Mouwase', 'jmx': 'Western Juxtlahuaca Mixtec', 'jna': 'Jangshung', 'jnd': 'Jandavra', 'jng': 'Yangman', 'jni': 'Janji', 'jnj': 'Yemsa', 'jnl': 'Rawat', 'jns': 'Jaunsari', 'job': 'Joba', 'jod': 'Wojenaka', 'jog': 'Jogi', 'jor': 'Jorá', 'jos': 'Jordanian Sign Language', 'jow': 'Jowulu', 'jpa': 'Jewish Palestinian Aramaic', 'jpn': 'Japanese', 'jpr': 'Judeo-Persian', 'jqr': 'Jaqaru', 'jra': 'Jarai', 'jrb': 'Judeo-Arabic', 'jrr': 'Jiru', 'jrt': 'Jorto', 'jru': 'Japrería', 'jsl': 'Japanese Sign Language', 'jua': 'Júma', 'jub': 'Wannu', 'juc': 'Jurchen', 'jud': 'Worodougou', 'juh': 'Hõne', 'jui': 'Ngadjuri', 'juk': 'Wapan', 'jul': 'Jirel', 'jum': 'Jumjum', 'jun': 'Juang', 'juo': 'Jiba', 'jup': 'Hupdë', 'jur': 'Jurúna', 'jus': 'Jumla Sign Language', 'jut': 'Jutish', 'juu': 'Ju', 'juw': 'Wãpha', 'juy': 'Juray', 'jvd': 'Javindo', 'jvn': 'Caribbean Javanese', 'jwi': 'Jwira-Pepesa', 'jya': 'Jiarong', 'jye': 'Judeo-Yemeni Arabic', 'jyy': 'Jaya', 'kaa': 'Kara-Kalpak', 'kab': 'Kabyle', 'kac': 'Kachin', 'kad': 'Adara', 'kae': 'Ketangalan', 'kaf': 'Katso', 'kag': 'Kajaman', 'kah': 'Kara (Central African Republic)', 'kai': 'Karekare', 'kaj': 'Jju', 'kak': 'Kalanguya', 'kal': 'Kalaallisut', 'kam': 'Kamba (Kenya)', 'kan': 'Kannada', 'kao': 'Xaasongaxango', 'kap': 'Bezhta', 'kaq': 'Capanahua', 'kas': 'Kashmiri', 'kat': 'Georgian', 'kau': 'Kanuri', 'kav': 'Katukína', 'kaw': 'Kawi', 'kax': 'Kao', 'kay': 'Kamayurá', 'kaz': 'Kazakh', 'kba': 'Kalarko', 'kbb': 'Kaxuiâna', 'kbc': 'Kadiwéu', 'kbd': 'Kabardian', 'kbe': 'Kanju', 'kbg': 'Khamba', 'kbh': 'Camsá', 'kbi': 'Kaptiau', 'kbj': 'Kari', 'kbk': 'Grass Koiari', 'kbl': 'Kanembu', 'kbm': 'Iwal', 'kbn': 'Kare (Central African Republic)', 'kbo': 'Keliko', 'kbp': 'Kabiyè', 'kbq': 'Kamano', 'kbr': 'Kafa', 'kbs': 'Kande', 'kbt': 'Abadi', 'kbu': 'Kabutra', 'kbv': 'Dera (Indonesia)', 'kbw': 'Kaiep', 'kbx': 'Ap Ma', 'kby': 'Manga Kanuri', 'kbz': 'Duhwa', 'kca': 'Khanty', 'kcb': 'Kawacha', 'kcc': 'Lubila', 'kcd': 'Ngkâlmpw Kanum', 'kce': 'Kaivi', 'kcf': 'Ukaan', 'kcg': 'Tyap', 'kch': 'Vono', 'kci': 'Kamantan', 'kcj': 'Kobiana', 'kck': 'Kalanga', 'kcl': 'Kela (Papua New Guinea)', 'kcm': 'Gula (Central African Republic)', 'kcn': 'Nubi', 'kco': 'Kinalakna', 'kcp': 'Kanga', 'kcq': 'Kamo', 'kcr': 'Katla', 'kcs': 'Koenoem', 'kct': 'Kaian', 'kcu': 'Kami (Tanzania)', 'kcv': 'Kete', 'kcw': 'Kabwari', 'kcx': 'Kachama-Ganjule', 'kcy': 'Korandje', 'kcz': 'Konongo', 'kda': 'Worimi', 'kdc': 'Kutu', 'kdd': 'Yankunytjatjara', 'kde': 'Makonde', 'kdf': 'Mamusi', 'kdg': 'Seba', 'kdh': 'Tem', 'kdi': 'Kumam', 'kdj': 'Karamojong', 'kdk': 'Numèè', 'kdl': 'Tsikimba', 'kdm': 'Kagoma', 'kdn': 'Kunda', 'kdp': 'Kaningdon-Nindem', 'kdq': 'Koch', 'kdr': 'Karaim', 'kdt': 'Kuy', 'kdu': 'Kadaru', 'kdw': 'Koneraw', 'kdx': 'Kam', 'kdy': 'Keder', 'kdz': 'Kwaja', 'kea': 'Kabuverdianu', 'keb': 'Kélé', 'kec': 'Keiga', 'ked': 'Kerewe', 'kee': 'Eastern Keres', 'kef': 'Kpessi', 'keg': 'Tese', 'keh': 'Keak', 'kei': 'Kei', 'kej': 'Kadar', 'kek': 'Kekchí', 'kel': 'Kela (Democratic Republic of Congo)', 'kem': 'Kemak', 'ken': 'Kenyang', 'keo': 'Kakwa', 'kep': 'Kaikadi', 'keq': 'Kamar', 'ker': 'Kera', 'kes': 'Kugbo', 'ket': 'Ket', 'keu': 'Akebu', 'kev': 'Kanikkaran', 'kew': 'West Kewa', 'kex': 'Kukna', 'key': 'Kupia', 'kez': 'Kukele', 'kfa': 'Kodava', 'kfb': 'Northwestern Kolami', 'kfc': 'Konda-Dora', 'kfd': 'Korra Koraga', 'kfe': 'Kota (India)', 'kff': 'Koya', 'kfg': 'Kudiya', 'kfh': 'Kurichiya', 'kfi': 'Kannada Kurumba', 'kfj': 'Kemiehua', 'kfk': 'Kinnauri', 'kfl': 'Kung', 'kfm': 'Khunsari', 'kfn': 'Kuk', 'kfo': "Koro (Côte d'Ivoire)", 'kfp': 'Korwa', 'kfq': 'Korku', 'kfr': 'Kachhi', 'kfs': 'Bilaspuri', 'kft': 'Kanjari', 'kfu': 'Katkari', 'kfv': 'Kurmukar', 'kfw': 'Kharam Naga', 'kfx': 'Kullu Pahari', 'kfy': 'Kumaoni', 'kfz': 'Koromfé', 'kga': 'Koyaga', 'kgb': 'Kawe', 'kgd': 'Kataang', 'kge': 'Komering', 'kgf': 'Kube', 'kgg': 'Kusunda', 'kgi': 'Selangor Sign Language', 'kgj': 'Gamale Kham', 'kgk': 'Kaiwá', 'kgl': 'Kunggari', 'kgm': 'Karipúna', 'kgn': 'Karingani', 'kgo': 'Krongo', 'kgp': 'Kaingang', 'kgq': 'Kamoro', 'kgr': 'Abun', 'kgs': 'Kumbainggar', 'kgt': 'Somyev', 'kgu': 'Kobol', 'kgv': 'Karas', 'kgw': 'Karon Dori', 'kgx': 'Kamaru', 'kgy': 'Kyerung', 'kha': 'Khasi', 'khb': 'Lü', 'khc': 'Tukang Besi North', 'khd': 'Bädi Kanum', 'khe': 'Korowai', 'khf': 'Khuen', 'khg': 'Khams Tibetan', 'khh': 'Kehu', 'khj': 'Kuturmi', 'khk': 'Halh Mongolian', 'khl': 'Lusi', 'khm': 'Central Khmer', 'khn': 'Khandesi', 'kho': 'Khotanese', 'khp': 'Kapori', 'khq': 'Koyra Chiini Songhay', 'khr': 'Kharia', 'khs': 'Kasua', 'kht': 'Khamti', 'khu': 'Nkhumbi', 'khv': 'Khvarshi', 'khw': 'Khowar', 'khx': 'Kanu', 'khy': 'Kele (Democratic Republic of Congo)', 'khz': 'Keapara', 'kia': 'Kim', 'kib': 'Koalib', 'kic': 'Kickapoo', 'kid': 'Koshin', 'kie': 'Kibet', 'kif': 'Eastern Parbate Kham', 'kig': 'Kimaama', 'kih': 'Kilmeri', 'kii': 'Kitsai', 'kij': 'Kilivila', 'kik': 'Kikuyu', 'kil': 'Kariya', 'kim': 'Karagas', 'kin': 'Kinyarwanda', 'kio': 'Kiowa', 'kip': 'Sheshi Kham', 'kiq': 'Kosadle', 'kir': 'Kirghiz', 'kis': 'Kis', 'kit': 'Agob', 'kiu': 'Kirmanjki (individual language)', 'kiv': 'Kimbu', 'kiw': 'Northeast Kiwai', 'kix': 'Khiamniungan Naga', 'kiy': 'Kirikiri', 'kiz': 'Kisi', 'kja': 'Mlap', 'kjb': "Q'anjob'al", 'kjc': 'Coastal Konjo', 'kjd': 'Southern Kiwai', 'kje': 'Kisar', 'kjf': 'Khalaj', 'kjg': 'Khmu', 'kjh': 'Khakas', 'kji': 'Zabana', 'kjj': 'Khinalugh', 'kjk': 'Highland Konjo', 'kjl': 'Western Parbate Kham', 'kjm': 'Kháng', 'kjn': 'Kunjen', 'kjo': 'Harijan Kinnauri', 'kjp': 'Pwo Eastern Karen', 'kjq': 'Western Keres', 'kjr': 'Kurudu', 'kjs': 'East Kewa', 'kjt': 'Phrae Pwo Karen', 'kju': 'Kashaya', 'kjv': 'Kaikavian Literary Language', 'kjx': 'Ramopa', 'kjy': 'Erave', 'kjz': 'Bumthangkha', 'kka': 'Kakanda', 'kkb': 'Kwerisa', 'kkc': 'Odoodee', 'kkd': 'Kinuku', 'kke': 'Kakabe', 'kkf': 'Kalaktang Monpa', 'kkg': 'Mabaka Valley Kalinga', 'kkh': 'Khün', 'kki': 'Kagulu', 'kkj': 'Kako', 'kkk': 'Kokota', 'kkl': 'Kosarek Yale', 'kkm': 'Kiong', 'kkn': 'Kon Keu', 'kko': 'Karko', 'kkp': 'Gugubera', 'kkq': 'Kaiku', 'kkr': 'Kir-Balar', 'kks': 'Giiwo', 'kkt': 'Koi', 'kku': 'Tumi', 'kkv': 'Kangean', 'kkw': 'Teke-Kukuya', 'kkx': 'Kohin', 'kky': 'Guguyimidjir', 'kkz': 'Kaska', 'kla': 'Klamath-Modoc', 'klb': 'Kiliwa', 'klc': 'Kolbila', 'kld': 'Gamilaraay', 'kle': 'Kulung (Nepal)', 'klf': 'Kendeje', 'klg': 'Tagakaulo', 'klh': 'Weliki', 'kli': 'Kalumpang', 'klj': 'Turkic Khalaj', 'klk': 'Kono (Nigeria)', 'kll': 'Kagan Kalagan', 'klm': 'Migum', 'kln': 'Kalenjin', 'klo': 'Kapya', 'klp': 'Kamasa', 'klq': 'Rumu', 'klr': 'Khaling', 'kls': 'Kalasha', 'klt': 'Nukna', 'klu': 'Klao', 'klv': 'Maskelynes', 'klw': 'Lindu', 'klx': 'Koluwawa', 'kly': 'Kalao', 'klz': 'Kabola', 'kma': 'Konni', 'kmb': 'Kimbundu', 'kmc': 'Southern Dong', 'kmd': 'Majukayang Kalinga', 'kme': 'Bakole', 'kmf': 'Kare (Papua New Guinea)', 'kmg': 'Kâte', 'kmh': 'Kalam', 'kmi': 'Kami (Nigeria)', 'kmj': 'Kumarbhag Paharia', 'kmk': 'Limos Kalinga', 'kml': 'Tanudan Kalinga', 'kmm': 'Kom (India)', 'kmn': 'Awtuw', 'kmo': 'Kwoma', 'kmp': 'Gimme', 'kmq': 'Kwama', 'kmr': 'Northern Kurdish', 'kms': 'Kamasau', 'kmt': 'Kemtuik', 'kmu': 'Kanite', 'kmv': 'Karipúna Creole French', 'kmw': 'Komo (Democratic Republic of Congo)', 'kmx': 'Waboda', 'kmy': 'Koma', 'kmz': 'Khorasani Turkish', 'kna': 'Dera (Nigeria)', 'knb': 'Lubuagan Kalinga', 'knc': 'Central Kanuri', 'knd': 'Konda', 'kne': 'Kankanaey', 'knf': 'Mankanya', 'kng': 'Koongo', 'kni': 'Kanufi', 'knj': 'Western Kanjobal', 'knk': 'Kuranko', 'knl': 'Keninjal', 'knm': 'Kanamarí', 'knn': 'Konkani (individual language)', 'kno': 'Kono (Sierra Leone)', 'knp': 'Kwanja', 'knq': 'Kintaq', 'knr': 'Kaningra', 'kns': 'Kensiu', 'knt': 'Panoan Katukína', 'knu': 'Kono (Guinea)', 'knv': 'Tabo', 'knw': 'Kung-Ekoka', 'knx': 'Kendayan', 'kny': 'Kanyok', 'knz': 'Kalamsé', 'koa': 'Konomala', 'koc': 'Kpati', 'kod': 'Kodi', 'koe': 'Kacipo-Balesi', 'kof': 'Kubi', 'kog': 'Cogui', 'koh': 'Koyo', 'koi': 'Komi-Permyak', 'kok': 'Konkani (macrolanguage)', 'kol': 'Kol (Papua New Guinea)', 'kom': 'Komi', 'kon': 'Kongo', 'koo': 'Konzo', 'kop': 'Waube', 'koq': 'Kota (Gabon)', 'kor': 'Korean', 'kos': 'Kosraean', 'kot': 'Lagwan', 'kou': 'Koke', 'kov': 'Kudu-Camo', 'kow': 'Kugama', 'koy': 'Koyukon', 'koz': 'Korak', 'kpa': 'Kutto', 'kpb': 'Mullu Kurumba', 'kpc': 'Curripaco', 'kpd': 'Koba', 'kpe': 'Kpelle', 'kpf': 'Komba', 'kpg': 'Kapingamarangi', 'kph': 'Kplang', 'kpi': 'Kofei', 'kpj': 'Karajá', 'kpk': 'Kpan', 'kpl': 'Kpala', 'kpm': 'Koho', 'kpn': 'Kepkiriwát', 'kpo': 'Ikposo', 'kpq': 'Korupun-Sela', 'kpr': 'Korafe-Yegha', 'kps': 'Tehit', 'kpt': 'Karata', 'kpu': 'Kafoa', 'kpv': 'Komi-Zyrian', 'kpw': 'Kobon', 'kpx': 'Mountain Koiali', 'kpy': 'Koryak', 'kpz': 'Kupsabiny', 'kqa': 'Mum', 'kqb': 'Kovai', 'kqc': 'Doromu-Koki', 'kqd': 'Koy Sanjaq Surat', 'kqe': 'Kalagan', 'kqf': 'Kakabai', 'kqg': 'Khe', 'kqh': 'Kisankasa', 'kqi': 'Koitabu', 'kqj': 'Koromira', 'kqk': 'Kotafon Gbe', 'kql': 'Kyenele', 'kqm': 'Khisa', 'kqn': 'Kaonde', 'kqo': 'Eastern Krahn', 'kqp': 'Kimré', 'kqq': 'Krenak', 'kqr': 'Kimaragang', 'kqs': 'Northern Kissi', 'kqt': 'Klias River Kadazan', 'kqu': 'Seroa', 'kqv': 'Okolod', 'kqw': 'Kandas', 'kqx': 'Mser', 'kqy': 'Koorete', 'kqz': 'Korana', 'kra': 'Kumhali', 'krb': 'Karkin', 'krc': 'Karachay-Balkar', 'krd': 'Kairui-Midiki', 'kre': 'Panará', 'krf': 'Koro (Vanuatu)', 'krh': 'Kurama', 'kri': 'Krio', 'krj': 'Kinaray-A', 'krk': 'Kerek', 'krl': 'Karelian', 'krm': 'Krim', 'krn': 'Sapo', 'krp': 'Korop', 'krr': "Kru'ng 2", 'krs': 'Gbaya (Sudan)', 'krt': 'Tumari Kanuri', 'kru': 'Kurukh', 'krv': 'Kavet', 'krw': 'Western Krahn', 'krx': 'Karon', 'kry': 'Kryts', 'krz': 'Sota Kanum', 'ksa': 'Shuwa-Zamani', 'ksb': 'Shambala', 'ksc': 'Southern Kalinga', 'ksd': 'Kuanua', 'kse': 'Kuni', 'ksf': 'Bafia', 'ksg': 'Kusaghe', 'ksh': 'Kölsch', 'ksi': 'Krisa', 'ksj': 'Uare', 'ksk': 'Kansa', 'ksl': 'Kumalu', 'ksm': 'Kumba', 'ksn': 'Kasiguranin', 'kso': 'Kofa', 'ksp': 'Kaba', 'ksq': 'Kwaami', 'ksr': 'Borong', 'kss': 'Southern Kisi', 'kst': 'Winyé', 'ksu': 'Khamyang', 'ksv': 'Kusu', 'ksw': "S'gaw Karen", 'ksx': 'Kedang', 'ksy': 'Kharia Thar', 'ksz': 'Kodaku', 'kta': 'Katua', 'ktb': 'Kambaata', 'ktc': 'Kholok', 'ktd': 'Kokata', 'kte': 'Nubri', 'ktf': 'Kwami', 'ktg': 'Kalkutung', 'kth': 'Karanga', 'kti': 'North Muyu', 'ktj': 'Plapo Krumen', 'ktk': 'Kaniet', 'ktl': 'Koroshi', 'ktm': 'Kurti', 'ktn': 'Karitiâna', 'kto': 'Kuot', 'ktp': 'Kaduo', 'ktq': 'Katabaga', 'kts': 'South Muyu', 'ktt': 'Ketum', 'ktu': 'Kituba (Democratic Republic of Congo)', 'ktv': 'Eastern Katu', 'ktw': 'Kato', 'ktx': 'Kaxararí', 'kty': 'Kango (Bas-Uélé District)', 'ktz': "Ju/'hoan", 'kua': 'Kuanyama', 'kub': 'Kutep', 'kuc': 'Kwinsu', 'kud': "'Auhelawa", 'kue': 'Kuman (Papua New Guinea)', 'kuf': 'Western Katu', 'kug': 'Kupa', 'kuh': 'Kushi', 'kui': 'Kuikúro-Kalapálo', 'kuj': 'Kuria', 'kuk': "Kepo'", 'kul': 'Kulere', 'kum': 'Kumyk', 'kun': 'Kunama', 'kuo': 'Kumukio', 'kup': 'Kunimaipa', 'kuq': 'Karipuna', 'kur': 'Kurdish', 'kus': 'Kusaal', 'kut': 'Kutenai', 'kuu': 'Upper Kuskokwim', 'kuv': 'Kur', 'kuw': 'Kpagua', 'kux': 'Kukatja', 'kuy': "Kuuku-Ya'u", 'kuz': 'Kunza', 'kva': 'Bagvalal', 'kvb': 'Kubu', 'kvc': 'Kove', 'kvd': 'Kui (Indonesia)', 'kve': 'Kalabakan', 'kvf': 'Kabalai', 'kvg': 'Kuni-Boazi', 'kvh': 'Komodo', 'kvi': 'Kwang', 'kvj': 'Psikye', 'kvk': 'Korean Sign Language', 'kvl': 'Kayaw', 'kvm': 'Kendem', 'kvn': 'Border Kuna', 'kvo': 'Dobel', 'kvp': 'Kompane', 'kvq': 'Geba Karen', 'kvr': 'Kerinci', 'kvt': 'Lahta Karen', 'kvu': 'Yinbaw Karen', 'kvv': 'Kola', 'kvw': 'Wersing', 'kvx': 'Parkari Koli', 'kvy': 'Yintale Karen', 'kvz': 'Tsakwambo', 'kwa': 'Dâw', 'kwb': 'Kwa', 'kwc': 'Likwala', 'kwd': 'Kwaio', 'kwe': 'Kwerba', 'kwf': "Kwara'ae", 'kwg': 'Sara Kaba Deme', 'kwh': 'Kowiai', 'kwi': 'Awa-Cuaiquer', 'kwj': 'Kwanga', 'kwk': 'Kwakiutl', 'kwl': 'Kofyar', 'kwm': 'Kwambi', 'kwn': 'Kwangali', 'kwo': 'Kwomtari', 'kwp': 'Kodia', 'kwr': 'Kwer', 'kws': 'Kwese', 'kwt': 'Kwesten', 'kwu': 'Kwakum', 'kwv': 'Sara Kaba Náà', 'kww': 'Kwinti', 'kwx': 'Khirwar', 'kwy': 'San Salvador Kongo', 'kwz': 'Kwadi', 'kxa': 'Kairiru', 'kxb': 'Krobu', 'kxc': 'Konso', 'kxd': 'Brunei', 'kxf': 'Manumanaw Karen', 'kxh': 'Karo (Ethiopia)', 'kxi': 'Keningau Murut', 'kxj': 'Kulfa', 'kxk': 'Zayein Karen', 'kxl': 'Nepali Kurux', 'kxm': 'Northern Khmer', 'kxn': 'Kanowit-Tanjong Melanau', 'kxo': 'Kanoé', 'kxp': 'Wadiyara Koli', 'kxq': 'Smärky Kanum', 'kxr': 'Koro (Papua New Guinea)', 'kxs': 'Kangjia', 'kxt': 'Koiwat', 'kxu': 'Kui (India)', 'kxv': 'Kuvi', 'kxw': 'Konai', 'kxx': 'Likuba', 'kxy': 'Kayong', 'kxz': 'Kerewo', 'kya': 'Kwaya', 'kyb': 'Butbut Kalinga', 'kyc': 'Kyaka', 'kyd': 'Karey', 'kye': 'Krache', 'kyf': 'Kouya', 'kyg': 'Keyagana', 'kyh': 'Karok', 'kyi': 'Kiput', 'kyj': 'Karao', 'kyk': 'Kamayo', 'kyl': 'Kalapuya', 'kym': 'Kpatili', 'kyn': 'Northern Binukidnon', 'kyo': 'Kelon', 'kyp': 'Kang', 'kyq': 'Kenga', 'kyr': 'Kuruáya', 'kys': 'Baram Kayan', 'kyt': 'Kayagar', 'kyu': 'Western Kayah', 'kyv': 'Kayort', 'kyw': 'Kudmali', 'kyx': 'Rapoisi', 'kyy': 'Kambaira', 'kyz': 'Kayabí', 'kza': 'Western Karaboro', 'kzb': 'Kaibobo', 'kzc': 'Bondoukou Kulango', 'kzd': 'Kadai', 'kze': 'Kosena', 'kzf': "Da'a Kaili", 'kzg': 'Kikai', 'kzi': 'Kelabit', 'kzk': 'Kazukuru', 'kzl': 'Kayeli', 'kzm': 'Kais', 'kzn': 'Kokola', 'kzo': 'Kaningi', 'kzp': 'Kaidipang', 'kzq': 'Kaike', 'kzr': 'Karang', 'kzs': 'Sugut Dusun', 'kzu': 'Kayupulau', 'kzv': 'Komyandaret', 'kzw': 'Karirí-Xocó', 'kzx': 'Kamarian', 'kzy': 'Kango (Tshopo District)', 'kzz': 'Kalabra', 'laa': 'Southern Subanen', 'lab': 'Linear A', 'lac': 'Lacandon', 'lad': 'Ladino', 'lae': 'Pattani', 'laf': 'Lafofa', 'lag': 'Langi', 'lah': 'Lahnda', 'lai': 'Lambya', 'laj': 'Lango (Uganda)', 'lak': 'Laka (Nigeria)', 'lal': 'Lalia', 'lam': 'Lamba', 'lan': 'Laru', 'lao': 'Lao', 'lap': 'Laka (Chad)', 'laq': 'Qabiao', 'lar': 'Larteh', 'las': 'Lama (Togo)', 'lat': 'Latin', 'lau': 'Laba', 'lav': 'Latvian', 'law': 'Lauje', 'lax': 'Tiwa', 'lay': 'Lama Bai', 'laz': 'Aribwatsa', 'lba': 'Lui', 'lbb': 'Label', 'lbc': 'Lakkia', 'lbe': 'Lak', 'lbf': 'Tinani', 'lbg': 'Laopang', 'lbi': "La'bi", 'lbj': 'Ladakhi', 'lbk': 'Central Bontok', 'lbl': 'Libon Bikol', 'lbm': 'Lodhi', 'lbn': 'Lamet', 'lbo': 'Laven', 'lbq': 'Wampar', 'lbr': 'Lohorung', 'lbs': 'Libyan Sign Language', 'lbt': 'Lachi', 'lbu': 'Labu', 'lbv': 'Lavatbura-Lamusong', 'lbw': 'Tolaki', 'lbx': 'Lawangan', 'lby': 'Lamu-Lamu', 'lbz': 'Lardil', 'lcc': 'Legenyem', 'lcd': 'Lola', 'lce': 'Loncong', 'lcf': 'Lubu', 'lch': 'Luchazi', 'lcl': 'Lisela', 'lcm': 'Tungag', 'lcp': 'Western Lawa', 'lcq': 'Luhu', 'lcs': 'Lisabata-Nuniali', 'lda': 'Kla-Dan', 'ldb': 'Dũya', 'ldd': 'Luri', 'ldg': 'Lenyima', 'ldh': 'Lamja-Dengsa-Tola', 'ldi': 'Laari', 'ldj': 'Lemoro', 'ldk': 'Leelau', 'ldl': 'Kaan', 'ldm': 'Landoma', 'ldn': 'Láadan', 'ldo': 'Loo', 'ldp': 'Tso', 'ldq': 'Lufu', 'lea': 'Lega-Shabunda', 'leb': 'Lala-Bisa', 'lec': 'Leco', 'led': 'Lendu', 'lee': 'Lyélé', 'lef': 'Lelemi', 'leh': 'Lenje', 'lei': 'Lemio', 'lej': 'Lengola', 'lek': 'Leipon', 'lel': 'Lele (Democratic Republic of Congo)', 'lem': 'Nomaande', 'len': 'Lenca', 'leo': 'Leti (Cameroon)', 'lep': 'Lepcha', 'leq': 'Lembena', 'ler': 'Lenkau', 'les': 'Lese', 'let': 'Lesing-Gelimi', 'leu': 'Kara (Papua New Guinea)', 'lev': 'Lamma', 'lew': 'Ledo Kaili', 'lex': 'Luang', 'ley': 'Lemolang', 'lez': 'Lezghian', 'lfa': 'Lefa', 'lfn': 'Lingua Franca Nova', 'lga': 'Lungga', 'lgb': 'Laghu', 'lgg': 'Lugbara', 'lgh': 'Laghuu', 'lgi': 'Lengilu', 'lgk': 'Lingarak', 'lgl': 'Wala', 'lgm': 'Lega-Mwenga', 'lgn': 'Opuuo', 'lgq': 'Logba', 'lgr': 'Lengo', 'lgt': 'Pahi', 'lgu': 'Longgu', 'lgz': 'Ligenza', 'lha': 'Laha (Viet Nam)', 'lhh': 'Laha (Indonesia)', 'lhi': 'Lahu Shi', 'lhl': 'Lahul Lohar', 'lhm': 'Lhomi', 'lhn': 'Lahanan', 'lhp': 'Lhokpu', 'lhs': 'Mlahsö', 'lht': 'Lo-Toga', 'lhu': 'Lahu', 'lia': 'West-Central Limba', 'lib': 'Likum', 'lic': 'Hlai', 'lid': 'Nyindrou', 'lie': 'Likila', 'lif': 'Limbu', 'lig': 'Ligbi', 'lih': 'Lihir', 'lij': 'Ligurian', 'lik': 'Lika', 'lil': 'Lillooet', 'lim': 'Limburgan', 'lin': 'Lingala', 'lio': 'Liki', 'lip': 'Sekpele', 'liq': 'Libido', 'lir': 'Liberian English', 'lis': 'Lisu', 'lit': 'Lithuanian', 'liu': 'Logorik', 'liv': 'Liv', 'liw': 'Col', 'lix': 'Liabuku', 'liy': 'Banda-Bambari', 'liz': 'Libinza', 'lja': 'Golpa', 'lje': 'Rampi', 'lji': 'Laiyolo', 'ljl': "Li'o", 'ljp': 'Lampung Api', 'ljw': 'Yirandali', 'ljx': 'Yuru', 'lka': 'Lakalei', 'lkb': 'Kabras', 'lkc': 'Kucong', 'lkd': 'Lakondê', 'lke': 'Kenyi', 'lkh': 'Lakha', 'lki': 'Laki', 'lkj': 'Remun', 'lkl': 'Laeko-Libuat', 'lkm': 'Kalaamaya', 'lkn': 'Lakon', 'lko': 'Khayo', 'lkr': 'Päri', 'lks': 'Kisa', 'lkt': 'Lakota', 'lku': 'Kungkari', 'lky': 'Lokoya', 'lla': 'Lala-Roba', 'llb': 'Lolo', 'llc': 'Lele (Guinea)', 'lld': 'Ladin', 'lle': 'Lele (Papua New Guinea)', 'llf': 'Hermit', 'llg': 'Lole', 'llh': 'Lamu', 'lli': 'Teke-Laali', 'llj': 'Ladji Ladji', 'llk': 'Lelak', 'lll': 'Lilau', 'llm': 'Lasalimu', 'lln': 'Lele (Chad)', 'llo': 'Khlor', 'llp': 'North Efate', 'llq': 'Lolak', 'lls': 'Lithuanian Sign Language', 'llu': 'Lau', 'llx': 'Lauan', 'lma': 'East Limba', 'lmb': 'Merei', 'lmc': 'Limilngan', 'lmd': 'Lumun', 'lme': 'Pévé', 'lmf': 'South Lembata', 'lmg': 'Lamogai', 'lmh': 'Lambichhong', 'lmi': 'Lombi', 'lmj': 'West Lembata', 'lmk': 'Lamkang', 'lml': 'Hano', 'lmn': 'Lambadi', 'lmo': 'Lombard', 'lmp': 'Limbum', 'lmq': 'Lamatuka', 'lmr': 'Lamalera', 'lmu': 'Lamenu', 'lmv': 'Lomaiviti', 'lmw': 'Lake Miwok', 'lmx': 'Laimbue', 'lmy': 'Lamboya', 'lmz': 'Lumbee', 'lna': 'Langbashe', 'lnb': 'Mbalanhu', 'lnd': 'Lundayeh', 'lng': 'Langobardic', 'lnh': 'Lanoh', 'lni': "Daantanai'", 'lnj': 'Leningitij', 'lnl': 'South Central Banda', 'lnm': 'Langam', 'lnn': 'Lorediakarkar', 'lno': 'Lango (Sudan)', 'lns': "Lamnso'", 'lnu': 'Longuda', 'lnw': 'Lanima', 'lnz': 'Lonzo', 'loa': 'Loloda', 'lob': 'Lobi', 'loc': 'Inonhan', 'loe': 'Saluan', 'lof': 'Logol', 'log': 'Logo', 'loh': 'Narim', 'loi': "Loma (Côte d'Ivoire)", 'loj': 'Lou', 'lok': 'Loko', 'lol': 'Mongo', 'lom': 'Loma (Liberia)', 'lon': 'Malawi Lomwe', 'loo': 'Lombo', 'lop': 'Lopa', 'loq': 'Lobala', 'lor': 'Téén', 'los': 'Loniu', 'lot': 'Otuho', 'lou': 'Louisiana Creole', 'lov': 'Lopi', 'low': 'Tampias Lobu', 'lox': 'Loun', 'loy': 'Loke', 'loz': 'Lozi', 'lpa': 'Lelepa', 'lpe': 'Lepki', 'lpn': 'Long Phuri Naga', 'lpo': 'Lipo', 'lpx': 'Lopit', 'lra': "Rara Bakati'", 'lrc': 'Northern Luri', 'lre': 'Laurentian', 'lrg': 'Laragia', 'lri': 'Marachi', 'lrk': 'Loarki', 'lrl': 'Lari', 'lrm': 'Marama', 'lrn': 'Lorang', 'lro': 'Laro', 'lrr': 'Southern Yamphu', 'lrt': 'Larantuka Malay', 'lrv': 'Larevat', 'lrz': 'Lemerig', 'lsa': 'Lasgerdi', 'lsd': 'Lishana Deni', 'lse': 'Lusengo', 'lsg': 'Lyons Sign Language', 'lsh': 'Lish', 'lsi': 'Lashi', 'lsl': 'Latvian Sign Language', 'lsm': 'Saamia', 'lso': 'Laos Sign Language', 'lsp': 'Panamanian Sign Language', 'lsr': 'Aruop', 'lss': 'Lasi', 'lst': 'Trinidad and Tobago Sign Language', 'lsy': 'Mauritian Sign Language', 'ltc': 'Late Middle Chinese', 'ltg': 'Latgalian', 'lti': 'Leti (Indonesia)', 'ltn': 'Latundê', 'lto': 'Tsotso', 'lts': 'Tachoni', 'ltu': 'Latu', 'ltz': 'Luxembourgish', 'lua': 'Luba-Lulua', 'lub': 'Luba-Katanga', 'luc': 'Aringa', 'lud': 'Ludian', 'lue': 'Luvale', 'luf': 'Laua', 'lug': 'Ganda', 'lui': 'Luiseno', 'luj': 'Luna', 'luk': 'Lunanakha', 'lul': "Olu'bo", 'lum': 'Luimbi', 'lun': 'Lunda', 'luo': 'Luo (Kenya and Tanzania)', 'lup': 'Lumbu', 'luq': 'Lucumi', 'lur': 'Laura', 'lus': 'Lushai', 'lut': 'Lushootseed', 'luu': 'Lumba-Yakkha', 'luv': 'Luwati', 'luw': 'Luo (Cameroon)', 'luy': 'Luyia', 'luz': 'Southern Luri', 'lva': "Maku'a", 'lvk': 'Lavukaleve', 'lvs': 'Standard Latvian', 'lvu': 'Levuka', 'lwa': 'Lwalu', 'lwe': 'Lewo Eleng', 'lwg': 'Wanga', 'lwh': 'White Lachi', 'lwl': 'Eastern Lawa', 'lwm': 'Laomian', 'lwo': 'Luwo', 'lwt': 'Lewotobi', 'lwu': 'Lawu', 'lww': 'Lewo', 'lya': 'Layakha', 'lyg': 'Lyngngam', 'lyn': 'Luyana', 'lzh': 'Literary Chinese', 'lzl': 'Litzlitz', 'lzn': 'Leinong Naga', 'lzz': 'Laz', 'maa': 'San Jerónimo Tecóatl Mazatec', 'mab': 'Yutanduchi Mixtec', 'mad': 'Madurese', 'mae': 'Bo-Rukul', 'maf': 'Mafa', 'mag': 'Magahi', 'mah': 'Marshallese', 'mai': 'Maithili', 'maj': 'Jalapa De Díaz Mazatec', 'mak': 'Makasar', 'mal': 'Malayalam', 'mam': 'Mam', 'man': 'Mandingo', 'maq': 'Chiquihuitlán Mazatec', 'mar': 'Marathi', 'mas': 'Masai', 'mat': 'San Francisco Matlatzinca', 'mau': 'Huautla Mazatec', 'mav': 'Sateré-Mawé', 'maw': 'Mampruli', 'max': 'North Moluccan Malay', 'maz': 'Central Mazahua', 'mba': 'Higaonon', 'mbb': 'Western Bukidnon Manobo', 'mbc': 'Macushi', 'mbd': 'Dibabawon Manobo', 'mbe': 'Molale', 'mbf': 'Baba Malay', 'mbh': 'Mangseng', 'mbi': 'Ilianen Manobo', 'mbj': 'Nadëb', 'mbk': 'Malol', 'mbl': 'Maxakalí', 'mbm': 'Ombamba', 'mbn': 'Macaguán', 'mbo': 'Mbo (Cameroon)', 'mbp': 'Malayo', 'mbq': 'Maisin', 'mbr': 'Nukak Makú', 'mbs': 'Sarangani Manobo', 'mbt': 'Matigsalug Manobo', 'mbu': 'Mbula-Bwazza', 'mbv': 'Mbulungish', 'mbw': 'Maring', 'mbx': 'Mari (East Sepik Province)', 'mby': 'Memoni', 'mbz': 'Amoltepec Mixtec', 'mca': 'Maca', 'mcb': 'Machiguenga', 'mcc': 'Bitur', 'mcd': 'Sharanahua', 'mce': 'Itundujia Mixtec', 'mcf': 'Matsés', 'mcg': 'Mapoyo', 'mch': 'Maquiritari', 'mci': 'Mese', 'mcj': 'Mvanip', 'mck': 'Mbunda', 'mcl': 'Macaguaje', 'mcm': 'Malaccan Creole Portuguese', 'mcn': 'Masana', 'mco': 'Coatlán Mixe', 'mcp': 'Makaa', 'mcq': 'Ese', 'mcr': 'Menya', 'mcs': 'Mambai', 'mct': 'Mengisa', 'mcu': 'Cameroon Mambila', 'mcv': 'Minanibai', 'mcw': 'Mawa (Chad)', 'mcx': 'Mpiemo', 'mcy': 'South Watut', 'mcz': 'Mawan', 'mda': 'Mada (Nigeria)', 'mdb': 'Morigi', 'mdc': 'Male (Papua New Guinea)', 'mdd': 'Mbum', 'mde': 'Maba (Chad)', 'mdf': 'Moksha', 'mdg': 'Massalat', 'mdh': 'Maguindanaon', 'mdi': 'Mamvu', 'mdj': 'Mangbetu', 'mdk': 'Mangbutu', 'mdl': 'Maltese Sign Language', 'mdm': 'Mayogo', 'mdn': 'Mbati', 'mdp': 'Mbala', 'mdq': 'Mbole', 'mdr': 'Mandar', 'mds': 'Maria (Papua New Guinea)', 'mdt': 'Mbere', 'mdu': 'Mboko', 'mdv': 'Santa Lucía Monteverde Mixtec', 'mdw': 'Mbosi', 'mdx': 'Dizin', 'mdy': 'Male (Ethiopia)', 'mdz': 'Suruí Do Pará', 'mea': 'Menka', 'meb': 'Ikobi', 'mec': 'Mara', 'med': 'Melpa', 'mee': 'Mengen', 'mef': 'Megam', 'meh': 'Southwestern Tlaxiaco Mixtec', 'mei': 'Midob', 'mej': 'Meyah', 'mek': 'Mekeo', 'mel': 'Central Melanau', 'mem': 'Mangala', 'men': 'Mende (Sierra Leone)', 'meo': 'Kedah Malay', 'mep': 'Miriwung', 'meq': 'Merey', 'mer': 'Meru', 'mes': 'Masmaje', 'met': 'Mato', 'meu': 'Motu', 'mev': 'Mano', 'mew': 'Maaka', 'mey': 'Hassaniyya', 'mez': 'Menominee', 'mfa': 'Pattani Malay', 'mfb': 'Bangka', 'mfc': 'Mba', 'mfd': 'Mendankwe-Nkwen', 'mfe': 'Morisyen', 'mff': 'Naki', 'mfg': 'Mogofin', 'mfh': 'Matal', 'mfi': 'Wandala', 'mfj': 'Mefele', 'mfk': 'North Mofu', 'mfl': 'Putai', 'mfm': 'Marghi South', 'mfn': 'Cross River Mbembe', 'mfo': 'Mbe', 'mfp': 'Makassar Malay', 'mfq': 'Moba', 'mfr': 'Marithiel', 'mfs': 'Mexican Sign Language', 'mft': 'Mokerang', 'mfu': 'Mbwela', 'mfv': 'Mandjak', 'mfw': 'Mulaha', 'mfx': 'Melo', 'mfy': 'Mayo', 'mfz': 'Mabaan', 'mga': 'Middle Irish (900-1200)', 'mgb': 'Mararit', 'mgc': 'Morokodo', 'mgd': 'Moru', 'mge': 'Mango', 'mgf': 'Maklew', 'mgg': 'Mpumpong', 'mgh': 'Makhuwa-Meetto', 'mgi': 'Lijili', 'mgj': 'Abureni', 'mgk': 'Mawes', 'mgl': 'Maleu-Kilenge', 'mgm': 'Mambae', 'mgn': 'Mbangi', 'mgo': "Meta'", 'mgp': 'Eastern Magar', 'mgq': 'Malila', 'mgr': 'Mambwe-Lungu', 'mgs': 'Manda (Tanzania)', 'mgt': 'Mongol', 'mgu': 'Mailu', 'mgv': 'Matengo', 'mgw': 'Matumbi', 'mgy': 'Mbunga', 'mgz': 'Mbugwe', 'mha': 'Manda (India)', 'mhb': 'Mahongwe', 'mhc': 'Mocho', 'mhd': 'Mbugu', 'mhe': 'Besisi', 'mhf': 'Mamaa', 'mhg': 'Margu', 'mhi': "Ma'di", 'mhj': 'Mogholi', 'mhk': 'Mungaka', 'mhl': 'Mauwake', 'mhm': 'Makhuwa-Moniga', 'mhn': 'Mócheno', 'mho': 'Mashi (Zambia)', 'mhp': 'Balinese Malay', 'mhq': 'Mandan', 'mhr': 'Eastern Mari', 'mhs': 'Buru (Indonesia)', 'mht': 'Mandahuaca', 'mhu': 'Digaro-Mishmi', 'mhw': 'Mbukushu', 'mhx': 'Maru', 'mhy': "Ma'anyan", 'mhz': 'Mor (Mor Islands)', 'mia': 'Miami', 'mib': 'Atatláhuca Mixtec', 'mic': "Mi'kmaq", 'mid': 'Mandaic', 'mie': 'Ocotepec Mixtec', 'mif': 'Mofu-Gudur', 'mig': 'San Miguel El Grande Mixtec', 'mih': 'Chayuco Mixtec', 'mii': 'Chigmecatitlán Mixtec', 'mij': 'Abar', 'mik': 'Mikasuki', 'mil': 'Peñoles Mixtec', 'mim': 'Alacatlatzala Mixtec', 'min': 'Minangkabau', 'mio': 'Pinotepa Nacional Mixtec', 'mip': 'Apasco-Apoala Mixtec', 'miq': 'Mískito', 'mir': 'Isthmus Mixe', 'mis': 'Uncoded languages', 'mit': 'Southern Puebla Mixtec', 'miu': 'Cacaloxtepec Mixtec', 'miw': 'Akoye', 'mix': 'Mixtepec Mixtec', 'miy': 'Ayutla Mixtec', 'miz': 'Coatzospan Mixtec', 'mjb': 'Makalero', 'mjc': 'San Juan Colorado Mixtec', 'mjd': 'Northwest Maidu', 'mje': 'Muskum', 'mjg': 'Tu', 'mjh': 'Mwera (Nyasa)', 'mji': 'Kim Mun', 'mjj': 'Mawak', 'mjk': 'Matukar', 'mjl': 'Mandeali', 'mjm': 'Medebur', 'mjn': 'Ma (Papua New Guinea)', 'mjo': 'Malankuravan', 'mjp': 'Malapandaram', 'mjq': 'Malaryan', 'mjr': 'Malavedan', 'mjs': 'Miship', 'mjt': 'Sauria Paharia', 'mju': 'Manna-Dora', 'mjv': 'Mannan', 'mjw': 'Karbi', 'mjx': 'Mahali', 'mjy': 'Mahican', 'mjz': 'Majhi', 'mka': 'Mbre', 'mkb': 'Mal Paharia', 'mkc': 'Siliput', 'mkd': 'Macedonian', 'mke': 'Mawchi', 'mkf': 'Miya', 'mkg': 'Mak (China)', 'mki': 'Dhatki', 'mkj': 'Mokilese', 'mkk': 'Byep', 'mkl': 'Mokole', 'mkm': 'Moklen', 'mkn': 'Kupang Malay', 'mko': 'Mingang Doso', 'mkp': 'Moikodi', 'mkq': 'Bay Miwok', 'mkr': 'Malas', 'mks': 'Silacayoapan Mixtec', 'mkt': 'Vamale', 'mku': 'Konyanka Maninka', 'mkv': 'Mafea', 'mkw': 'Kituba (Congo)', 'mkx': 'Kinamiging Manobo', 'mky': 'East Makian', 'mkz': 'Makasae', 'mla': 'Malo', 'mlb': 'Mbule', 'mlc': 'Cao Lan', 'mle': 'Manambu', 'mlf': 'Mal', 'mlg': 'Malagasy', 'mlh': 'Mape', 'mli': 'Malimpung', 'mlj': 'Miltu', 'mlk': 'Ilwana', 'mll': 'Malua Bay', 'mlm': 'Mulam', 'mln': 'Malango', 'mlo': 'Mlomp', 'mlp': 'Bargam', 'mlq': 'Western Maninkakan', 'mlr': 'Vame', 'mls': 'Masalit', 'mlt': 'Maltese', 'mlu': "To'abaita", 'mlv': 'Motlav', 'mlw': 'Moloko', 'mlx': 'Malfaxal', 'mlz': 'Malaynon', 'mma': 'Mama', 'mmb': 'Momina', 'mmc': 'Michoacán Mazahua', 'mmd': 'Maonan', 'mme': 'Mae', 'mmf': 'Mundat', 'mmg': 'North Ambrym', 'mmh': 'Mehináku', 'mmi': 'Musar', 'mmj': 'Majhwar', 'mmk': 'Mukha-Dora', 'mml': 'Man Met', 'mmm': 'Maii', 'mmn': 'Mamanwa', 'mmo': 'Mangga Buang', 'mmp': 'Siawi', 'mmq': 'Musak', 'mmr': 'Western Xiangxi Miao', 'mmt': 'Malalamai', 'mmu': 'Mmaala', 'mmv': 'Miriti', 'mmw': 'Emae', 'mmx': 'Madak', 'mmy': 'Migaama', 'mmz': 'Mabaale', 'mna': 'Mbula', 'mnb': 'Muna', 'mnc': 'Manchu', 'mnd': 'Mondé', 'mne': 'Naba', 'mnf': 'Mundani', 'mng': 'Eastern Mnong', 'mnh': 'Mono (Democratic Republic of Congo)', 'mni': 'Manipuri', 'mnj': 'Munji', 'mnk': 'Mandinka', 'mnl': 'Tiale', 'mnm': 'Mapena', 'mnn': 'Southern Mnong', 'mnp': 'Min Bei Chinese', 'mnq': 'Minriq', 'mnr': 'Mono (USA)', 'mns': 'Mansi', 'mnu': 'Mer', 'mnv': 'Rennell-Bellona', 'mnw': 'Mon', 'mnx': 'Manikion', 'mny': 'Manyawa', 'mnz': 'Moni', 'moa': 'Mwan', 'moc': 'Mocoví', 'mod': 'Mobilian', 'moe': 'Montagnais', 'mog': 'Mongondow', 'moh': 'Mohawk', 'moi': 'Mboi', 'moj': 'Monzombo', 'mok': 'Morori', 'mom': 'Mangue', 'mon': 'Mongolian', 'moo': 'Monom', 'mop': 'Mopán Maya', 'moq': 'Mor (Bomberai Peninsula)', 'mor': 'Moro', 'mos': 'Mossi', 'mot': 'Barí', 'mou': 'Mogum', 'mov': 'Mohave', 'mow': 'Moi (Congo)', 'mox': 'Molima', 'moy': 'Shekkacho', 'moz': 'Mukulu', 'mpa': 'Mpoto', 'mpb': 'Mullukmulluk', 'mpc': 'Mangarayi', 'mpd': 'Machinere', 'mpe': 'Majang', 'mpg': 'Marba', 'mph': 'Maung', 'mpi': 'Mpade', 'mpj': 'Martu Wangka', 'mpk': 'Mbara (Chad)', 'mpl': 'Middle Watut', 'mpm': 'Yosondúa Mixtec', 'mpn': 'Mindiri', 'mpo': 'Miu', 'mpp': 'Migabac', 'mpq': 'Matís', 'mpr': 'Vangunu', 'mps': 'Dadibi', 'mpt': 'Mian', 'mpu': 'Makuráp', 'mpv': 'Mungkip', 'mpw': 'Mapidian', 'mpx': 'Misima-Panaeati', 'mpy': 'Mapia', 'mpz': 'Mpi', 'mqa': 'Maba (Indonesia)', 'mqb': 'Mbuko', 'mqc': 'Mangole', 'mqe': 'Matepi', 'mqf': 'Momuna', 'mqg': 'Kota Bangun Kutai Malay', 'mqh': 'Tlazoyaltepec Mixtec', 'mqi': 'Mariri', 'mqj': 'Mamasa', 'mqk': 'Rajah Kabunsuwan Manobo', 'mql': 'Mbelime', 'mqm': 'South Marquesan', 'mqn': 'Moronene', 'mqo': 'Modole', 'mqp': 'Manipa', 'mqq': 'Minokok', 'mqr': 'Mander', 'mqs': 'West Makian', 'mqt': 'Mok', 'mqu': 'Mandari', 'mqv': 'Mosimo', 'mqw': 'Murupi', 'mqx': 'Mamuju', 'mqy': 'Manggarai', 'mqz': 'Pano', 'mra': 'Mlabri', 'mrb': 'Marino', 'mrc': 'Maricopa', 'mrd': 'Western Magar', 'mre': "Martha's Vineyard Sign Language", 'mrf': 'Elseng', 'mrg': 'Mising', 'mrh': 'Mara Chin', 'mri': 'Maori', 'mrj': 'Western Mari', 'mrk': 'Hmwaveke', 'mrl': 'Mortlockese', 'mrm': 'Merlav', 'mrn': 'Cheke Holo', 'mro': 'Mru', 'mrp': 'Morouas', 'mrq': 'North Marquesan', 'mrr': 'Maria (India)', 'mrs': 'Maragus', 'mrt': 'Marghi Central', 'mru': 'Mono (Cameroon)', 'mrv': 'Mangareva', 'mrw': 'Maranao', 'mrx': 'Maremgi', 'mry': 'Mandaya', 'mrz': 'Marind', 'msa': 'Malay (macrolanguage)', 'msb': 'Masbatenyo', 'msc': 'Sankaran Maninka', 'msd': 'Yucatec Maya Sign Language', 'mse': 'Musey', 'msf': 'Mekwei', 'msg': 'Moraid', 'msh': 'Masikoro Malagasy', 'msi': 'Sabah Malay', 'msj': 'Ma (Democratic Republic of Congo)', 'msk': 'Mansaka', 'msl': 'Molof', 'msm': 'Agusan Manobo', 'msn': 'Vurës', 'mso': 'Mombum', 'msp': 'Maritsauá', 'msq': 'Caac', 'msr': 'Mongolian Sign Language', 'mss': 'West Masela', 'msu': 'Musom', 'msv': 'Maslam', 'msw': 'Mansoanka', 'msx': 'Moresada', 'msy': 'Aruamu', 'msz': 'Momare', 'mta': 'Cotabato Manobo', 'mtb': 'Anyin Morofo', 'mtc': 'Munit', 'mtd': 'Mualang', 'mte': 'Mono (Solomon Islands)', 'mtf': 'Murik (Papua New Guinea)', 'mtg': 'Una', 'mth': 'Munggui', 'mti': 'Maiwa (Papua New Guinea)', 'mtj': 'Moskona', 'mtk': "Mbe'", 'mtl': 'Montol', 'mtm': 'Mator', 'mtn': 'Matagalpa', 'mto': 'Totontepec Mixe', 'mtp': 'Wichí Lhamtés Nocten', 'mtq': 'Muong', 'mtr': 'Mewari', 'mts': 'Yora', 'mtt': 'Mota', 'mtu': 'Tututepec Mixtec', 'mtv': "Asaro'o", 'mtw': 'Southern Binukidnon', 'mtx': 'Tidaá Mixtec', 'mty': 'Nabi', 'mua': 'Mundang', 'mub': 'Mubi', 'muc': 'Ajumbu', 'mud': 'Mednyj Aleut', 'mue': 'Media Lengua', 'mug': 'Musgu', 'muh': 'Mündü', 'mui': 'Musi', 'muj': 'Mabire', 'muk': 'Mugom', 'mul': 'Multiple languages', 'mum': 'Maiwala', 'muo': 'Nyong', 'mup': 'Malvi', 'muq': 'Eastern Xiangxi Miao', 'mur': 'Murle', 'mus': 'Creek', 'mut': 'Western Muria', 'muu': 'Yaaku', 'muv': 'Muthuvan', 'mux': 'Bo-Ung', 'muy': 'Muyang', 'muz': 'Mursi', 'mva': 'Manam', 'mvb': 'Mattole', 'mvd': 'Mamboru', 'mve': 'Marwari (Pakistan)', 'mvf': 'Peripheral Mongolian', 'mvg': 'Yucuañe Mixtec', 'mvh': 'Mulgi', 'mvi': 'Miyako', 'mvk': 'Mekmek', 'mvl': 'Mbara (Australia)', 'mvm': 'Muya', 'mvn': 'Minaveha', 'mvo': 'Marovo', 'mvp': 'Duri', 'mvq': 'Moere', 'mvr': 'Marau', 'mvs': 'Massep', 'mvt': 'Mpotovoro', 'mvu': 'Marfa', 'mvv': 'Tagal Murut', 'mvw': 'Machinga', 'mvx': 'Meoswar', 'mvy': 'Indus Kohistani', 'mvz': 'Mesqan', 'mwa': 'Mwatebu', 'mwb': 'Juwal', 'mwc': 'Are', 'mwe': 'Mwera (Chimwera)', 'mwf': 'Murrinh-Patha', 'mwg': 'Aiklep', 'mwh': 'Mouk-Aria', 'mwi': 'Labo', 'mwk': 'Kita Maninkakan', 'mwl': 'Mirandese', 'mwm': 'Sar', 'mwn': 'Nyamwanga', 'mwo': 'Central Maewo', 'mwp': 'Kala Lagaw Ya', 'mwq': 'Mün Chin', 'mwr': 'Marwari', 'mws': 'Mwimbi-Muthambi', 'mwt': 'Moken', 'mwu': 'Mittu', 'mwv': 'Mentawai', 'mww': 'Hmong Daw', 'mwx': 'Mediak', 'mwy': 'Mosiro', 'mwz': 'Moingi', 'mxa': 'Northwest Oaxaca Mixtec', 'mxb': 'Tezoatlán Mixtec', 'mxc': 'Manyika', 'mxd': 'Modang', 'mxe': 'Mele-Fila', 'mxf': 'Malgbe', 'mxg': 'Mbangala', 'mxh': 'Mvuba', 'mxi': 'Mozarabic', 'mxj': 'Miju-Mishmi', 'mxk': 'Monumbo', 'mxl': 'Maxi Gbe', 'mxm': 'Meramera', 'mxn': 'Moi (Indonesia)', 'mxo': 'Mbowe', 'mxp': 'Tlahuitoltepec Mixe', 'mxq': 'Juquila Mixe', 'mxr': 'Murik (Malaysia)', 'mxs': 'Huitepec Mixtec', 'mxt': 'Jamiltepec Mixtec', 'mxu': 'Mada (Cameroon)', 'mxv': 'Metlatónoc Mixtec', 'mxw': 'Namo', 'mxx': 'Mahou', 'mxy': 'Southeastern Nochixtlán Mixtec', 'mxz': 'Central Masela', 'mya': 'Burmese', 'myb': 'Mbay', 'myc': 'Mayeka', 'myd': 'Maramba', 'mye': 'Myene', 'myf': 'Bambassi', 'myg': 'Manta', 'myh': 'Makah', 'myi': 'Mina (India)', 'myj': 'Mangayat', 'myk': 'Mamara Senoufo', 'myl': 'Moma', 'mym': "Me'en", 'myo': 'Anfillo', 'myp': 'Pirahã', 'myr': 'Muniche', 'mys': 'Mesmes', 'myu': 'Mundurukú', 'myv': 'Erzya', 'myw': 'Muyuw', 'myx': 'Masaaba', 'myy': 'Macuna', 'myz': 'Classical Mandaic', 'mza': 'Santa María Zacatepec Mixtec', 'mzb': 'Tumzabt', 'mzc': 'Madagascar Sign Language', 'mzd': 'Malimba', 'mze': 'Morawa', 'mzg': 'Monastic Sign Language', 'mzh': 'Wichí Lhamtés Güisnay', 'mzi': 'Ixcatlán Mazatec', 'mzj': 'Manya', 'mzk': 'Nigeria Mambila', 'mzl': 'Mazatlán Mixe', 'mzm': 'Mumuye', 'mzn': 'Mazanderani', 'mzo': 'Matipuhy', 'mzp': 'Movima', 'mzq': 'Mori Atas', 'mzr': 'Marúbo', 'mzs': 'Macanese', 'mzt': 'Mintil', 'mzu': 'Inapang', 'mzv': 'Manza', 'mzw': 'Deg', 'mzx': 'Mawayana', 'mzy': 'Mozambican Sign Language', 'mzz': 'Maiadomu', 'naa': 'Namla', 'nab': 'Southern Nambikuára', 'nac': 'Narak', 'nae': "Naka'ela", 'naf': 'Nabak', 'nag': 'Naga Pidgin', 'naj': 'Nalu', 'nak': 'Nakanai', 'nal': 'Nalik', 'nam': "Ngan'gityemerri", 'nan': 'Min Nan Chinese', 'nao': 'Naaba', 'nap': 'Neapolitan', 'naq': 'Khoekhoe', 'nar': 'Iguta', 'nas': 'Naasioi', 'nat': 'Ca̱hungwa̱rya̱', 'nau': 'Nauru', 'nav': 'Navajo', 'naw': 'Nawuri', 'nax': 'Nakwi', 'nay': 'Narrinyeri', 'naz': 'Coatepec Nahuatl', 'nba': 'Nyemba', 'nbb': 'Ndoe', 'nbc': 'Chang Naga', 'nbd': 'Ngbinda', 'nbe': 'Konyak Naga', 'nbg': 'Nagarchal', 'nbh': 'Ngamo', 'nbi': 'Mao Naga', 'nbj': 'Ngarinman', 'nbk': 'Nake', 'nbl': 'South Ndebele', 'nbm': "Ngbaka Ma'bo", 'nbn': 'Kuri', 'nbo': 'Nkukoli', 'nbp': 'Nnam', 'nbq': 'Nggem', 'nbr': 'Numana-Nunku-Gbantu-Numbu', 'nbs': 'Namibian Sign Language', 'nbt': 'Na', 'nbu': 'Rongmei Naga', 'nbv': 'Ngamambo', 'nbw': 'Southern Ngbandi', 'nby': 'Ningera', 'nca': 'Iyo', 'ncb': 'Central Nicobarese', 'ncc': 'Ponam', 'ncd': 'Nachering', 'nce': 'Yale', 'ncf': 'Notsi', 'ncg': "Nisga'a", 'nch': 'Central Huasteca Nahuatl', 'nci': 'Classical Nahuatl', 'ncj': 'Northern Puebla Nahuatl', 'nck': 'Nakara', 'ncl': 'Michoacán Nahuatl', 'ncm': 'Nambo', 'ncn': 'Nauna', 'nco': 'Sibe', 'ncp': 'Ndaktup', 'ncr': 'Ncane', 'ncs': 'Nicaraguan Sign Language', 'nct': 'Chothe Naga', 'ncu': 'Chumburung', 'ncx': 'Central Puebla Nahuatl', 'ncz': 'Natchez', 'nda': 'Ndasa', 'ndb': 'Kenswei Nsei', 'ndc': 'Ndau', 'ndd': 'Nde-Nsele-Nta', 'nde': 'North Ndebele', 'ndf': 'Nadruvian', 'ndg': 'Ndengereko', 'ndh': 'Ndali', 'ndi': 'Samba Leko', 'ndj': 'Ndamba', 'ndk': 'Ndaka', 'ndl': 'Ndolo', 'ndm': 'Ndam', 'ndn': 'Ngundi', 'ndo': 'Ndonga', 'ndp': 'Ndo', 'ndq': 'Ndombe', 'ndr': 'Ndoola', 'nds': 'Low German', 'ndt': 'Ndunga', 'ndu': 'Dugun', 'ndv': 'Ndut', 'ndw': 'Ndobo', 'ndx': 'Nduga', 'ndy': 'Lutos', 'ndz': 'Ndogo', 'nea': "Eastern Ngad'a", 'neb': "Toura (Côte d'Ivoire)", 'nec': 'Nedebang', 'ned': 'Nde-Gbite', 'nee': 'Nêlêmwa-Nixumwak', 'nef': 'Nefamese', 'neg': 'Negidal', 'neh': 'Nyenkha', 'nei': 'Neo-Hittite', 'nej': 'Neko', 'nek': 'Neku', 'nem': 'Nemi', 'nen': 'Nengone', 'neo': 'Ná-Meo', 'nep': 'Nepali (macrolanguage)', 'neq': 'North Central Mixe', 'ner': 'Yahadian', 'nes': 'Bhoti Kinnauri', 'net': 'Nete', 'neu': 'Neo', 'nev': 'Nyaheun', 'new': 'Newari', 'nex': 'Neme', 'ney': 'Neyo', 'nez': 'Nez Perce', 'nfa': 'Dhao', 'nfd': 'Ahwai', 'nfl': 'Ayiwo', 'nfr': 'Nafaanra', 'nfu': 'Mfumte', 'nga': 'Ngbaka', 'ngb': 'Northern Ngbandi', 'ngc': 'Ngombe (Democratic Republic of Congo)', 'ngd': 'Ngando (Central African Republic)', 'nge': 'Ngemba', 'ngg': 'Ngbaka Manza', 'ngh': 'N/u', 'ngi': 'Ngizim', 'ngj': 'Ngie', 'ngk': 'Dalabon', 'ngl': 'Lomwe', 'ngm': "Ngatik Men's Creole", 'ngn': 'Ngwo', 'ngo': 'Ngoni', 'ngp': 'Ngulu', 'ngq': 'Ngurimi', 'ngr': 'Engdewu', 'ngs': 'Gvoko', 'ngt': 'Ngeq', 'ngu': 'Guerrero Nahuatl', 'ngv': 'Nagumi', 'ngw': 'Ngwaba', 'ngx': 'Nggwahyi', 'ngy': 'Tibea', 'ngz': 'Ngungwel', 'nha': 'Nhanda', 'nhb': 'Beng', 'nhc': 'Tabasco Nahuatl', 'nhd': 'Chiripá', 'nhe': 'Eastern Huasteca Nahuatl', 'nhf': 'Nhuwala', 'nhg': 'Tetelcingo Nahuatl', 'nhh': 'Nahari', 'nhi': 'Zacatlán-Ahuacatlán-Tepetzintla Nahuatl', 'nhk': 'Isthmus-Cosoleacaque Nahuatl', 'nhm': 'Morelos Nahuatl', 'nhn': 'Central Nahuatl', 'nho': 'Takuu', 'nhp': 'Isthmus-Pajapan Nahuatl', 'nhq': 'Huaxcaleca Nahuatl', 'nhr': 'Naro', 'nht': 'Ometepec Nahuatl', 'nhu': 'Noone', 'nhv': 'Temascaltepec Nahuatl', 'nhw': 'Western Huasteca Nahuatl', 'nhx': 'Isthmus-Mecayapan Nahuatl', 'nhy': 'Northern Oaxaca Nahuatl', 'nhz': 'Santa María La Alta Nahuatl', 'nia': 'Nias', 'nib': 'Nakame', 'nid': 'Ngandi', 'nie': 'Niellim', 'nif': 'Nek', 'nig': 'Ngalakan', 'nih': 'Nyiha (Tanzania)', 'nii': 'Nii', 'nij': 'Ngaju', 'nik': 'Southern Nicobarese', 'nil': 'Nila', 'nim': 'Nilamba', 'nin': 'Ninzo', 'nio': 'Nganasan', 'niq': 'Nandi', 'nir': 'Nimboran', 'nis': 'Nimi', 'nit': 'Southeastern Kolami', 'niu': 'Niuean', 'niv': 'Gilyak', 'niw': 'Nimo', 'nix': 'Hema', 'niy': 'Ngiti', 'niz': 'Ningil', 'nja': 'Nzanyi', 'njb': 'Nocte Naga', 'njd': 'Ndonde Hamba', 'njh': 'Lotha Naga', 'nji': 'Gudanji', 'njj': 'Njen', 'njl': 'Njalgulgule', 'njm': 'Angami Naga', 'njn': 'Liangmai Naga', 'njo': 'Ao Naga', 'njr': 'Njerep', 'njs': 'Nisa', 'njt': 'Ndyuka-Trio Pidgin', 'nju': 'Ngadjunmaya', 'njx': 'Kunyi', 'njy': 'Njyem', 'njz': 'Nyishi', 'nka': 'Nkoya', 'nkb': 'Khoibu Naga', 'nkc': 'Nkongho', 'nkd': 'Koireng', 'nke': 'Duke', 'nkf': 'Inpui Naga', 'nkg': 'Nekgini', 'nkh': 'Khezha Naga', 'nki': 'Thangal Naga', 'nkj': 'Nakai', 'nkk': 'Nokuku', 'nkm': 'Namat', 'nkn': 'Nkangala', 'nko': 'Nkonya', 'nkp': 'Niuatoputapu', 'nkq': 'Nkami', 'nkr': 'Nukuoro', 'nks': 'North Asmat', 'nkt': 'Nyika (Tanzania)', 'nku': 'Bouna Kulango', 'nkv': 'Nyika (Malawi and Zambia)', 'nkw': 'Nkutu', 'nkx': 'Nkoroo', 'nkz': 'Nkari', 'nla': 'Ngombale', 'nlc': 'Nalca', 'nld': 'Dutch', 'nle': 'East Nyala', 'nlg': 'Gela', 'nli': 'Grangali', 'nlj': 'Nyali', 'nlk': 'Ninia Yali', 'nll': 'Nihali', 'nlo': 'Ngul', 'nlq': 'Lao Naga', 'nlu': 'Nchumbulu', 'nlv': 'Orizaba Nahuatl', 'nlw': 'Walangama', 'nlx': 'Nahali', 'nly': 'Nyamal', 'nlz': 'Nalögo', 'nma': 'Maram Naga', 'nmb': 'Big Nambas', 'nmc': 'Ngam', 'nmd': 'Ndumu', 'nme': 'Mzieme Naga', 'nmf': 'Tangkhul Naga (India)', 'nmg': 'Kwasio', 'nmh': 'Monsang Naga', 'nmi': 'Nyam', 'nmj': 'Ngombe (Central African Republic)', 'nmk': 'Namakura', 'nml': 'Ndemli', 'nmm': 'Manangba', 'nmn': '!Xóõ', 'nmo': 'Moyon Naga', 'nmp': 'Nimanbur', 'nmq': 'Nambya', 'nmr': 'Nimbari', 'nms': 'Letemboi', 'nmt': 'Namonuito', 'nmu': 'Northeast Maidu', 'nmv': 'Ngamini', 'nmw': 'Nimoa', 'nmx': 'Nama (Papua New Guinea)', 'nmy': 'Namuyi', 'nmz': 'Nawdm', 'nna': 'Nyangumarta', 'nnb': 'Nande', 'nnc': 'Nancere', 'nnd': 'West Ambae', 'nne': 'Ngandyera', 'nnf': 'Ngaing', 'nng': 'Maring Naga', 'nnh': 'Ngiemboon', 'nni': 'North Nuaulu', 'nnj': 'Nyangatom', 'nnk': 'Nankina', 'nnl': 'Northern Rengma Naga', 'nnm': 'Namia', 'nnn': 'Ngete', 'nno': 'Norwegian Nynorsk', 'nnp': 'Wancho Naga', 'nnq': 'Ngindo', 'nnr': 'Narungga', 'nns': 'Ningye', 'nnt': 'Nanticoke', 'nnu': 'Dwang', 'nnv': 'Nugunu (Australia)', 'nnw': 'Southern Nuni', 'nny': 'Nyangga', 'nnz': "Nda'nda'", 'noa': 'Woun Meu', 'nob': 'Norwegian Bokmål', 'noc': 'Nuk', 'nod': 'Northern Thai', 'noe': 'Nimadi', 'nof': 'Nomane', 'nog': 'Nogai', 'noh': 'Nomu', 'noi': 'Noiri', 'noj': 'Nonuya', 'nok': 'Nooksack', 'nol': 'Nomlaki', 'nom': 'Nocamán', 'non': 'Old Norse', 'nop': 'Numanggang', 'noq': 'Ngongo', 'nor': 'Norwegian', 'nos': 'Eastern Nisu', 'not': 'Nomatsiguenga', 'nou': 'Ewage-Notu', 'nov': 'Novial', 'now': 'Nyambo', 'noy': 'Noy', 'noz': 'Nayi', 'npa': 'Nar Phu', 'npb': 'Nupbikha', 'npg': 'Ponyo-Gongwang Naga', 'nph': 'Phom Naga', 'npi': 'Nepali (individual language)', 'npl': 'Southeastern Puebla Nahuatl', 'npn': 'Mondropolon', 'npo': 'Pochuri Naga', 'nps': 'Nipsan', 'npu': 'Puimei Naga', 'npy': 'Napu', 'nqg': 'Southern Nago', 'nqk': 'Kura Ede Nago', 'nqm': 'Ndom', 'nqn': 'Nen', 'nqo': "N'Ko", 'nqq': 'Kyan-Karyaw Naga', 'nqy': 'Akyaung Ari Naga', 'nra': 'Ngom', 'nrb': 'Nara', 'nrc': 'Noric', 'nre': 'Southern Rengma Naga', 'nrf': 'Jèrriais', 'nrg': 'Narango', 'nri': 'Chokri Naga', 'nrk': 'Ngarla', 'nrl': 'Ngarluma', 'nrm': 'Narom', 'nrn': 'Norn', 'nrp': 'North Picene', 'nrr': 'Norra', 'nrt': 'Northern Kalapuya', 'nru': 'Narua', 'nrx': 'Ngurmbur', 'nrz': 'Lala', 'nsa': 'Sangtam Naga', 'nsc': 'Nshi', 'nsd': 'Southern Nisu', 'nse': 'Nsenga', 'nsf': 'Northwestern Nisu', 'nsg': 'Ngasa', 'nsh': 'Ngoshie', 'nsi': 'Nigerian Sign Language', 'nsk': 'Naskapi', 'nsl': 'Norwegian Sign Language', 'nsm': 'Sumi Naga', 'nsn': 'Nehan', 'nso': 'Pedi', 'nsp': 'Nepalese Sign Language', 'nsq': 'Northern Sierra Miwok', 'nsr': 'Maritime Sign Language', 'nss': 'Nali', 'nst': 'Tase Naga', 'nsu': 'Sierra Negra Nahuatl', 'nsv': 'Southwestern Nisu', 'nsw': 'Navut', 'nsx': 'Nsongo', 'nsy': 'Nasal', 'nsz': 'Nisenan', 'ntd': 'Northern Tidung', 'nte': 'Nathembo', 'ntg': 'Ngantangarra', 'nti': 'Natioro', 'ntj': 'Ngaanyatjarra', 'ntk': 'Ikoma-Nata-Isenye', 'ntm': 'Nateni', 'nto': 'Ntomba', 'ntp': 'Northern Tepehuan', 'ntr': 'Delo', 'ntu': 'Natügu', 'ntw': 'Nottoway', 'ntx': 'Tangkhul Naga (Myanmar)', 'nty': 'Mantsi', 'ntz': 'Natanzi', 'nua': 'Yuanga', 'nuc': 'Nukuini', 'nud': 'Ngala', 'nue': 'Ngundu', 'nuf': 'Nusu', 'nug': 'Nungali', 'nuh': 'Ndunda', 'nui': 'Ngumbi', 'nuj': 'Nyole', 'nuk': 'Nuu-chah-nulth', 'nul': 'Nusa Laut', 'num': "Niuafo'ou", 'nun': 'Anong', 'nuo': 'Nguôn', 'nup': 'Nupe-Nupe-Tako', 'nuq': 'Nukumanu', 'nur': 'Nukuria', 'nus': 'Nuer', 'nut': 'Nung (Viet Nam)', 'nuu': 'Ngbundu', 'nuv': 'Northern Nuni', 'nuw': 'Nguluwan', 'nux': 'Mehek', 'nuy': 'Nunggubuyu', 'nuz': 'Tlamacazapa Nahuatl', 'nvh': 'Nasarian', 'nvm': 'Namiae', 'nvo': 'Nyokon', 'nwa': 'Nawathinehena', 'nwb': 'Nyabwa', 'nwc': 'Classical Newari', 'nwe': 'Ngwe', 'nwg': 'Ngayawung', 'nwi': 'Southwest Tanna', 'nwm': 'Nyamusa-Molo', 'nwo': 'Nauo', 'nwr': 'Nawaru', 'nwx': 'Middle Newar', 'nwy': 'Nottoway-Meherrin', 'nxa': 'Nauete', 'nxd': 'Ngando (Democratic Republic of Congo)', 'nxe': 'Nage', 'nxg': "Ngad'a", 'nxi': 'Nindi', 'nxk': 'Koki Naga', 'nxl': 'South Nuaulu', 'nxm': 'Numidian', 'nxn': 'Ngawun', 'nxo': 'Ndambomo', 'nxq': 'Naxi', 'nxr': 'Ninggerum', 'nxu': 'Narau', 'nxx': 'Nafri', 'nya': 'Nyanja', 'nyb': 'Nyangbo', 'nyc': 'Nyanga-li', 'nyd': 'Nyore', 'nye': 'Nyengo', 'nyf': 'Giryama', 'nyg': 'Nyindu', 'nyh': 'Nyigina', 'nyi': 'Ama (Sudan)', 'nyj': 'Nyanga', 'nyk': 'Nyaneka', 'nyl': 'Nyeu', 'nym': 'Nyamwezi', 'nyn': 'Nyankole', 'nyo': 'Nyoro', 'nyp': "Nyang'i", 'nyq': 'Nayini', 'nyr': 'Nyiha (Malawi)', 'nys': 'Nyunga', 'nyt': 'Nyawaygi', 'nyu': 'Nyungwe', 'nyv': 'Nyulnyul', 'nyw': 'Nyaw', 'nyx': 'Nganyaywana', 'nyy': 'Nyakyusa-Ngonde', 'nza': 'Tigon Mbembe', 'nzb': 'Njebi', 'nzi': 'Nzima', 'nzk': 'Nzakara', 'nzm': 'Zeme Naga', 'nzs': 'New Zealand Sign Language', 'nzu': 'Teke-Nzikou', 'nzy': 'Nzakambay', 'nzz': 'Nanga Dama Dogon', 'oaa': 'Orok', 'oac': 'Oroch', 'oar': 'Old Aramaic (up to 700 BCE)', 'oav': 'Old Avar', 'obi': 'Obispeño', 'obk': 'Southern Bontok', 'obl': 'Oblo', 'obm': 'Moabite', 'obo': 'Obo Manobo', 'obr': 'Old Burmese', 'obt': 'Old Breton', 'obu': 'Obulom', 'oca': 'Ocaina', 'och': 'Old Chinese', 'oci': 'Occitan (post 1500)', 'oco': 'Old Cornish', 'ocu': 'Atzingo Matlatzinca', 'oda': 'Odut', 'odk': 'Od', 'odt': 'Old Dutch', 'odu': 'Odual', 'ofo': 'Ofo', 'ofs': 'Old Frisian', 'ofu': 'Efutop', 'ogb': 'Ogbia', 'ogc': 'Ogbah', 'oge': 'Old Georgian', 'ogg': 'Ogbogolo', 'ogo': 'Khana', 'ogu': 'Ogbronuagum', 'oht': 'Old Hittite', 'ohu': 'Old Hungarian', 'oia': 'Oirata', 'oin': 'Inebu One', 'ojb': 'Northwestern Ojibwa', 'ojc': 'Central Ojibwa', 'ojg': 'Eastern Ojibwa', 'oji': 'Ojibwa', 'ojp': 'Old Japanese', 'ojs': 'Severn Ojibwa', 'ojv': 'Ontong Java', 'ojw': 'Western Ojibwa', 'oka': 'Okanagan', 'okb': 'Okobo', 'okd': 'Okodia', 'oke': 'Okpe (Southwestern Edo)', 'okg': 'Koko Babangk', 'okh': 'Koresh-e Rostam', 'oki': 'Okiek', 'okj': 'Oko-Juwoi', 'okk': 'Kwamtim One', 'okl': 'Old Kentish Sign Language', 'okm': 'Middle Korean (10th-16th cent.)', 'okn': 'Oki-No-Erabu', 'oko': 'Old Korean (3rd-9th cent.)', 'okr': 'Kirike', 'oks': 'Oko-Eni-Osayen', 'oku': 'Oku', 'okv': 'Orokaiva', 'okx': 'Okpe (Northwestern Edo)', 'ola': 'Walungge', 'old': 'Mochi', 'ole': 'Olekha', 'olk': 'Olkol', 'olm': 'Oloma', 'olo': 'Livvi', 'olr': 'Olrat', 'olt': 'Old Lithuanian', 'olu': 'Kuvale', 'oma': 'Omaha-Ponca', 'omb': 'East Ambae', 'omc': 'Mochica', 'omg': 'Omagua', 'omi': 'Omi', 'omk': 'Omok', 'oml': 'Ombo', 'omn': 'Minoan', 'omo': 'Utarmbung', 'omp': 'Old Manipuri', 'omr': 'Old Marathi', 'omt': 'Omotik', 'omu': 'Omurano', 'omw': 'South Tairora', 'omx': 'Old Mon', 'ona': 'Ona', 'onb': 'Lingao', 'one': 'Oneida', 'ong': 'Olo', 'oni': 'Onin', 'onj': 'Onjob', 'onk': 'Kabore One', 'onn': 'Onobasulu', 'ono': 'Onondaga', 'onp': 'Sartang', 'onr': 'Northern One', 'ons': 'Ono', 'ont': 'Ontenu', 'onu': 'Unua', 'onw': 'Old Nubian', 'onx': 'Onin Based Pidgin', 'ood': "Tohono O'odham", 'oog': 'Ong', 'oon': 'Önge', 'oor': 'Oorlams', 'oos': 'Old Ossetic', 'opa': 'Okpamheri', 'opk': 'Kopkaka', 'opm': 'Oksapmin', 'opo': 'Opao', 'opt': 'Opata', 'opy': 'Ofayé', 'ora': 'Oroha', 'orc': 'Orma', 'ore': 'Orejón', 'org': 'Oring', 'orh': 'Oroqen', 'ori': 'Oriya (macrolanguage)', 'orm': 'Oromo', 'orn': 'Orang Kanaq', 'oro': 'Orokolo', 'orr': 'Oruma', 'ors': 'Orang Seletar', 'ort': 'Adivasi Oriya', 'oru': 'Ormuri', 'orv': 'Old Russian', 'orw': 'Oro Win', 'orx': 'Oro', 'ory': 'Odia', 'orz': 'Ormu', 'osa': 'Osage', 'osc': 'Oscan', 'osi': 'Osing', 'oso': 'Ososo', 'osp': 'Old Spanish', 'oss': 'Ossetian', 'ost': 'Osatu', 'osu': 'Southern One', 'osx': 'Old Saxon', 'ota': 'Ottoman Turkish (1500-1928)', 'otb': 'Old Tibetan', 'otd': 'Ot Danum', 'ote': 'Mezquital Otomi', 'oti': 'Oti', 'otk': 'Old Turkish', 'otl': 'Tilapa Otomi', 'otm': 'Eastern Highland Otomi', 'otn': 'Tenango Otomi', 'otq': 'Querétaro Otomi', 'otr': 'Otoro', 'ots': 'Estado de México Otomi', 'ott': 'Temoaya Otomi', 'otu': 'Otuke', 'otw': 'Ottawa', 'otx': 'Texcatepec Otomi', 'oty': 'Old Tamil', 'otz': 'Ixtenco Otomi', 'oua': 'Tagargrent', 'oub': 'Glio-Oubi', 'oue': 'Oune', 'oui': 'Old Uighur', 'oum': 'Ouma', 'owi': 'Owiniga', 'owl': 'Old Welsh', 'oyb': 'Oy', 'oyd': 'Oyda', 'oym': 'Wayampi', 'oyy': "Oya'oya", 'ozm': 'Koonzime', 'pab': 'Parecís', 'pac': 'Pacoh', 'pad': 'Paumarí', 'pae': 'Pagibete', 'paf': 'Paranawát', 'pag': 'Pangasinan', 'pah': 'Tenharim', 'pai': 'Pe', 'pak': 'Parakanã', 'pal': 'Pahlavi', 'pam': 'Pampanga', 'pan': 'Panjabi', 'pao': 'Northern Paiute', 'pap': 'Papiamento', 'paq': 'Parya', 'par': 'Panamint', 'pas': 'Papasena', 'pat': 'Papitalai', 'pau': 'Palauan', 'pav': 'Pakaásnovos', 'paw': 'Pawnee', 'pax': 'Pankararé', 'pay': 'Pech', 'paz': 'Pankararú', 'pbb': 'Páez', 'pbc': 'Patamona', 'pbe': 'Mezontla Popoloca', 'pbf': 'Coyotepec Popoloca', 'pbg': 'Paraujano', 'pbh': "E'ñapa Woromaipu", 'pbi': 'Parkwa', 'pbl': 'Mak (Nigeria)', 'pbn': 'Kpasam', 'pbo': 'Papel', 'pbp': 'Badyara', 'pbr': 'Pangwa', 'pbs': 'Central Pame', 'pbt': 'Southern Pashto', 'pbu': 'Northern Pashto', 'pbv': 'Pnar', 'pby': 'Pyu (Papua New Guinea)', 'pca': 'Santa Inés Ahuatempan Popoloca', 'pcb': 'Pear', 'pcc': 'Bouyei', 'pcd': 'Picard', 'pce': 'Ruching Palaung', 'pcf': 'Paliyan', 'pcg': 'Paniya', 'pch': 'Pardhan', 'pci': 'Duruwa', 'pcj': 'Parenga', 'pck': 'Paite Chin', 'pcl': 'Pardhi', 'pcm': 'Nigerian Pidgin', 'pcn': 'Piti', 'pcp': 'Pacahuara', 'pcw': 'Pyapun', 'pda': 'Anam', 'pdc': 'Pennsylvania German', 'pdi': 'Pa Di', 'pdn': 'Podena', 'pdo': 'Padoe', 'pdt': 'Plautdietsch', 'pdu': 'Kayan', 'pea': 'Peranakan Indonesian', 'peb': 'Eastern Pomo', 'ped': 'Mala (Papua New Guinea)', 'pee': 'Taje', 'pef': 'Northeastern Pomo', 'peg': 'Pengo', 'peh': 'Bonan', 'pei': 'Chichimeca-Jonaz', 'pej': 'Northern Pomo', 'pek': 'Penchal', 'pel': 'Pekal', 'pem': 'Phende', 'peo': 'Old Persian (ca. 600-400 B.C.)', 'pep': 'Kunja', 'peq': 'Southern Pomo', 'pes': 'Iranian Persian', 'pev': 'Pémono', 'pex': 'Petats', 'pey': 'Petjo', 'pez': 'Eastern Penan', 'pfa': 'Pááfang', 'pfe': 'Peere', 'pfl': 'Pfaelzisch', 'pga': 'Sudanese Creole Arabic', 'pgd': 'Gāndhārī', 'pgg': 'Pangwali', 'pgi': 'Pagi', 'pgk': 'Rerep', 'pgl': 'Primitive Irish', 'pgn': 'Paelignian', 'pgs': 'Pangseng', 'pgu': 'Pagu', 'pgz': 'Papua New Guinean Sign Language', 'pha': 'Pa-Hng', 'phd': 'Phudagi', 'phg': 'Phuong', 'phh': 'Phukha', 'phk': 'Phake', 'phl': 'Phalura', 'phm': 'Phimbi', 'phn': 'Phoenician', 'pho': 'Phunoi', 'phq': "Phana'", 'phr': 'Pahari-Potwari', 'pht': 'Phu Thai', 'phu': 'Phuan', 'phv': 'Pahlavani', 'phw': 'Phangduwali', 'pia': 'Pima Bajo', 'pib': 'Yine', 'pic': 'Pinji', 'pid': 'Piaroa', 'pie': 'Piro', 'pif': 'Pingelapese', 'pig': 'Pisabo', 'pih': 'Pitcairn-Norfolk', 'pii': 'Pini', 'pij': 'Pijao', 'pil': 'Yom', 'pim': 'Powhatan', 'pin': 'Piame', 'pio': 'Piapoco', 'pip': 'Pero', 'pir': 'Piratapuyo', 'pis': 'Pijin', 'pit': 'Pitta Pitta', 'piu': 'Pintupi-Luritja', 'piv': 'Pileni', 'piw': 'Pimbwe', 'pix': 'Piu', 'piy': 'Piya-Kwonci', 'piz': 'Pije', 'pjt': 'Pitjantjatjara', 'pka': 'Ardhamāgadhī Prākrit', 'pkb': 'Pokomo', 'pkc': 'Paekche', 'pkg': 'Pak-Tong', 'pkh': 'Pankhu', 'pkn': 'Pakanha', 'pko': 'Pökoot', 'pkp': 'Pukapuka', 'pkr': 'Attapady Kurumba', 'pks': 'Pakistan Sign Language', 'pkt': 'Maleng', 'pku': 'Paku', 'pla': 'Miani', 'plb': 'Polonombauk', 'plc': 'Central Palawano', 'pld': 'Polari', 'ple': "Palu'e", 'plg': 'Pilagá', 'plh': 'Paulohi', 'pli': 'Pali', 'plj': 'Polci', 'plk': 'Kohistani Shina', 'pll': 'Shwe Palaung', 'pln': 'Palenquero', 'plo': 'Oluta Popoluca', 'plp': 'Palpa', 'plq': 'Palaic', 'plr': 'Palaka Senoufo', 'pls': 'San Marcos Tlacoyalco Popoloca', 'plt': 'Plateau Malagasy', 'plu': 'Palikúr', 'plv': 'Southwest Palawano', 'plw': "Brooke's Point Palawano", 'ply': 'Bolyu', 'plz': 'Paluan', 'pma': 'Paama', 'pmb': 'Pambia', 'pmd': 'Pallanganmiddang', 'pme': 'Pwaamei', 'pmf': 'Pamona', 'pmh': 'Māhārāṣṭri Prākrit', 'pmi': 'Northern Pumi', 'pmj': 'Southern Pumi', 'pmk': 'Pamlico', 'pml': 'Lingua Franca', 'pmm': 'Pomo', 'pmn': 'Pam', 'pmo': 'Pom', 'pmq': 'Northern Pame', 'pmr': 'Paynamar', 'pms': 'Piemontese', 'pmt': 'Tuamotuan', 'pmw': 'Plains Miwok', 'pmx': 'Poumei Naga', 'pmy': 'Papuan Malay', 'pmz': 'Southern Pame', 'pna': 'Punan Bah-Biau', 'pnb': 'Western Panjabi', 'pnc': 'Pannei', 'pne': 'Western Penan', 'png': 'Pongu', 'pnh': 'Penrhyn', 'pni': 'Aoheng', 'pnj': 'Pinjarup', 'pnk': 'Paunaka', 'pnl': 'Paleni', 'pnm': 'Punan Batu 1', 'pnn': 'Pinai-Hagahai', 'pno': 'Panobo', 'pnp': 'Pancana', 'pnq': 'Pana (Burkina Faso)', 'pnr': 'Panim', 'pns': 'Ponosakan', 'pnt': 'Pontic', 'pnu': 'Jiongnai Bunu', 'pnv': 'Pinigura', 'pnw': 'Panytyima', 'pnx': 'Phong-Kniang', 'pny': 'Pinyin', 'pnz': 'Pana (Central African Republic)', 'poc': 'Poqomam', 'poe': 'San Juan Atzingo Popoloca', 'pof': 'Poke', 'pog': 'Potiguára', 'poh': "Poqomchi'", 'poi': 'Highland Popoluca', 'pok': 'Pokangá', 'pol': 'Polish', 'pom': 'Southeastern Pomo', 'pon': 'Pohnpeian', 'poo': 'Central Pomo', 'pop': 'Pwapwâ', 'poq': 'Texistepec Popoluca', 'por': 'Portuguese', 'pos': 'Sayula Popoluca', 'pot': 'Potawatomi', 'pov': 'Upper Guinea Crioulo', 'pow': 'San Felipe Otlaltepec Popoloca', 'pox': 'Polabian', 'poy': 'Pogolo', 'ppe': 'Papi', 'ppi': 'Paipai', 'ppk': 'Uma', 'ppl': 'Pipil', 'ppm': 'Papuma', 'ppn': 'Papapana', 'ppo': 'Folopa', 'ppp': 'Pelende', 'ppq': 'Pei', 'pps': 'San Luís Temalacayuca Popoloca', 'ppt': 'Pare', 'ppu': 'Papora', 'pqa': "Pa'a", 'pqm': 'Malecite-Passamaquoddy', 'prb': "Lua'", 'prc': 'Parachi', 'prd': 'Parsi-Dari', 'pre': 'Principense', 'prf': 'Paranan', 'prg': 'Prussian', 'prh': 'Porohanon', 'pri': 'Paicî', 'prk': 'Parauk', 'prl': 'Peruvian Sign Language', 'prm': 'Kibiri', 'prn': 'Prasuni', 'pro': 'Old Provençal (to 1500)', 'prp': 'Parsi', 'prq': 'Ashéninka Perené', 'prr': 'Puri', 'prs': 'Dari', 'prt': 'Phai', 'pru': 'Puragi', 'prw': 'Parawen', 'prx': 'Purik', 'prz': 'Providencia Sign Language', 'psa': 'Asue Awyu', 'psc': 'Persian Sign Language', 'psd': 'Plains Indian Sign Language', 'pse': 'Central Malay', 'psg': 'Penang Sign Language', 'psh': 'Southwest Pashai', 'psi': 'Southeast Pashai', 'psl': 'Puerto Rican Sign Language', 'psm': 'Pauserna', 'psn': 'Panasuan', 'pso': 'Polish Sign Language', 'psp': 'Philippine Sign Language', 'psq': 'Pasi', 'psr': 'Portuguese Sign Language', 'pss': 'Kaulong', 'pst': 'Central Pashto', 'psu': 'Sauraseni Prākrit', 'psw': 'Port Sandwich', 'psy': 'Piscataway', 'pta': 'Pai Tavytera', 'pth': 'Pataxó Hã-Ha-Hãe', 'pti': 'Pintiini', 'ptn': 'Patani', 'pto': "Zo'é", 'ptp': 'Patep', 'ptq': 'Pattapu', 'ptr': 'Piamatsina', 'ptt': 'Enrekang', 'ptu': 'Bambam', 'ptv': 'Port Vato', 'ptw': 'Pentlatch', 'pty': 'Pathiya', 'pua': 'Western Highland Purepecha', 'pub': 'Purum', 'puc': 'Punan Merap', 'pud': 'Punan Aput', 'pue': 'Puelche', 'puf': 'Punan Merah', 'pug': 'Phuie', 'pui': 'Puinave', 'puj': 'Punan Tubu', 'puk': 'Pu Ko', 'pum': 'Puma', 'puo': 'Puoc', 'pup': 'Pulabu', 'puq': 'Puquina', 'pur': 'Puruborá', 'pus': 'Pushto', 'put': 'Putoh', 'puu': 'Punu', 'puw': 'Puluwatese', 'pux': 'Puare', 'puy': 'Purisimeño', 'pwa': 'Pawaia', 'pwb': 'Panawa', 'pwg': 'Gapapaiwa', 'pwi': 'Patwin', 'pwm': 'Molbog', 'pwn': 'Paiwan', 'pwo': 'Pwo Western Karen', 'pwr': 'Powari', 'pww': 'Pwo Northern Karen', 'pxm': 'Quetzaltepec Mixe', 'pye': 'Pye Krumen', 'pym': 'Fyam', 'pyn': 'Poyanáwa', 'pys': 'Paraguayan Sign Language', 'pyu': 'Puyuma', 'pyx': 'Pyu (Myanmar)', 'pyy': 'Pyen', 'pzn': 'Para Naga', 'qua': 'Quapaw', 'qub': 'Huallaga Huánuco Quechua', 'quc': "K'iche'", 'qud': 'Calderón Highland Quichua', 'que': 'Quechua', 'quf': 'Lambayeque Quechua', 'qug': 'Chimborazo Highland Quichua', 'quh': 'South Bolivian Quechua', 'qui': 'Quileute', 'quk': 'Chachapoyas Quechua', 'qul': 'North Bolivian Quechua', 'qum': 'Sipacapense', 'qun': 'Quinault', 'qup': 'Southern Pastaza Quechua', 'quq': 'Quinqui', 'qur': 'Yanahuanca Pasco Quechua', 'qus': 'Santiago del Estero Quichua', 'quv': 'Sacapulteco', 'quw': 'Tena Lowland Quichua', 'qux': 'Yauyos Quechua', 'quy': 'Ayacucho Quechua', 'quz': 'Cusco Quechua', 'qva': 'Ambo-Pasco Quechua', 'qvc': 'Cajamarca Quechua', 'qve': 'Eastern Apurímac Quechua', 'qvh': 'Huamalíes-Dos de Mayo Huánuco Quechua', 'qvi': 'Imbabura Highland Quichua', 'qvj': 'Loja Highland Quichua', 'qvl': 'Cajatambo North Lima Quechua', 'qvm': 'Margos-Yarowilca-Lauricocha Quechua', 'qvn': 'North Junín Quechua', 'qvo': 'Napo Lowland Quechua', 'qvp': 'Pacaraos Quechua', 'qvs': 'San Martín Quechua', 'qvw': 'Huaylla Wanca Quechua', 'qvy': 'Queyu', 'qvz': 'Northern Pastaza Quichua', 'qwa': 'Corongo Ancash Quechua', 'qwc': 'Classical Quechua', 'qwh': 'Huaylas Ancash Quechua', 'qwm': 'Kuman (Russia)', 'qws': 'Sihuas Ancash Quechua', 'qwt': 'Kwalhioqua-Tlatskanai', 'qxa': 'Chiquián Ancash Quechua', 'qxc': 'Chincha Quechua', 'qxh': 'Panao Huánuco Quechua', 'qxl': 'Salasaca Highland Quichua', 'qxn': 'Northern Conchucos Ancash Quechua', 'qxo': 'Southern Conchucos Ancash Quechua', 'qxp': 'Puno Quechua', 'qxq': "Qashqa'i", 'qxr': 'Cañar Highland Quichua', 'qxs': 'Southern Qiang', 'qxt': 'Santa Ana de Tusi Pasco Quechua', 'qxu': 'Arequipa-La Unión Quechua', 'qxw': 'Jauja Wanca Quechua', 'qya': 'Quenya', 'qyp': 'Quiripi', 'raa': 'Dungmali', 'rab': 'Camling', 'rac': 'Rasawa', 'rad': 'Rade', 'raf': 'Western Meohang', 'rag': 'Logooli', 'rah': 'Rabha', 'rai': 'Ramoaaina', 'raj': 'Rajasthani', 'rak': 'Tulu-Bohuai', 'ral': 'Ralte', 'ram': 'Canela', 'ran': 'Riantana', 'rao': 'Rao', 'rap': 'Rapanui', 'raq': 'Saam', 'rar': 'Rarotongan', 'ras': 'Tegali', 'rat': 'Razajerdi', 'rau': 'Raute', 'rav': 'Sampang', 'raw': 'Rawang', 'rax': 'Rang', 'ray': 'Rapa', 'raz': 'Rahambuu', 'rbb': 'Rumai Palaung', 'rbk': 'Northern Bontok', 'rbl': 'Miraya Bikol', 'rbp': 'Barababaraba', 'rcf': 'Réunion Creole French', 'rdb': 'Rudbari', 'rea': 'Rerau', 'reb': 'Rembong', 'ree': 'Rejang Kayan', 'reg': 'Kara (Tanzania)', 'rei': 'Reli', 'rej': 'Rejang', 'rel': 'Rendille', 'rem': 'Remo', 'ren': 'Rengao', 'rer': 'Rer Bare', 'res': 'Reshe', 'ret': 'Retta', 'rey': 'Reyesano', 'rga': 'Roria', 'rge': 'Romano-Greek', 'rgk': 'Rangkas', 'rgn': 'Romagnol', 'rgr': 'Resígaro', 'rgs': 'Southern Roglai', 'rgu': 'Ringgou', 'rhg': 'Rohingya', 'rhp': 'Yahang', 'ria': 'Riang (India)', 'rie': 'Rien', 'rif': 'Tarifit', 'ril': 'Riang (Myanmar)', 'rim': 'Nyaturu', 'rin': 'Nungu', 'rir': 'Ribun', 'rit': 'Ritarungo', 'riu': 'Riung', 'rjg': 'Rajong', 'rji': 'Raji', 'rjs': 'Rajbanshi', 'rka': 'Kraol', 'rkb': 'Rikbaktsa', 'rkh': 'Rakahanga-Manihiki', 'rki': 'Rakhine', 'rkm': 'Marka', 'rkt': 'Rangpuri', 'rkw': 'Arakwal', 'rma': 'Rama', 'rmb': 'Rembarunga', 'rmc': 'Carpathian Romani', 'rmd': 'Traveller Danish', 'rme': 'Angloromani', 'rmf': 'Kalo Finnish Romani', 'rmg': 'Traveller Norwegian', 'rmh': 'Murkim', 'rmi': 'Lomavren', 'rmk': 'Romkun', 'rml': 'Baltic Romani', 'rmm': 'Roma', 'rmn': 'Balkan Romani', 'rmo': 'Sinte Romani', 'rmp': 'Rempi', 'rmq': 'Caló', 'rms': 'Romanian Sign Language', 'rmt': 'Domari', 'rmu': 'Tavringer Romani', 'rmv': 'Romanova', 'rmw': 'Welsh Romani', 'rmx': 'Romam', 'rmy': 'Vlax Romani', 'rmz': 'Marma', 'rnd': 'Ruund', 'rng': 'Ronga', 'rnl': 'Ranglong', 'rnn': 'Roon', 'rnp': 'Rongpo', 'rnr': 'Nari Nari', 'rnw': 'Rungwa', 'rob': "Tae'", 'roc': 'Cacgia Roglai', 'rod': 'Rogo', 'roe': 'Ronji', 'rof': 'Rombo', 'rog': 'Northern Roglai', 'roh': 'Romansh', 'rol': 'Romblomanon', 'rom': 'Romany', 'ron': 'Romanian', 'roo': 'Rotokas', 'rop': 'Kriol', 'ror': 'Rongga', 'rou': 'Runga', 'row': 'Dela-Oenale', 'rpn': 'Repanbitip', 'rpt': 'Rapting', 'rri': 'Ririo', 'rro': 'Waima', 'rrt': 'Arritinngithigh', 'rsb': 'Romano-Serbian', 'rsi': 'Rennellese Sign Language', 'rsl': 'Russian Sign Language', 'rsm': 'Miriwoong Sign Language', 'rtc': 'Rungtu Chin', 'rth': 'Ratahan', 'rtm': 'Rotuman', 'rts': 'Yurats', 'rtw': 'Rathawi', 'rub': 'Gungu', 'ruc': 'Ruuli', 'rue': 'Rusyn', 'ruf': 'Luguru', 'rug': 'Roviana', 'ruh': 'Ruga', 'rui': 'Rufiji', 'ruk': 'Che', 'run': 'Rundi', 'ruo': 'Istro Romanian', 'rup': 'Macedo-Romanian', 'ruq': 'Megleno Romanian', 'rus': 'Russian', 'rut': 'Rutul', 'ruu': 'Lanas Lobu', 'ruy': 'Mala (Nigeria)', 'ruz': 'Ruma', 'rwa': 'Rawo', 'rwk': 'Rwa', 'rwm': 'Amba (Uganda)', 'rwo': 'Rawa', 'rwr': 'Marwari (India)', 'rxd': 'Ngardi', 'rxw': 'Karuwali', 'ryn': 'Northern Amami-Oshima', 'rys': 'Yaeyama', 'ryu': 'Central Okinawan', 'rzh': 'Rāziḥī', 'saa': 'Saba', 'sab': 'Buglere', 'sac': 'Meskwaki', 'sad': 'Sandawe', 'sae': 'Sabanê', 'saf': 'Safaliba', 'sag': 'Sango', 'sah': 'Yakut', 'saj': 'Sahu', 'sak': 'Sake', 'sam': 'Samaritan Aramaic', 'san': 'Sanskrit', 'sao': 'Sause', 'saq': 'Samburu', 'sar': 'Saraveca', 'sas': 'Sasak', 'sat': 'Santali', 'sau': 'Saleman', 'sav': 'Saafi-Saafi', 'saw': 'Sawi', 'sax': 'Sa', 'say': 'Saya', 'saz': 'Saurashtra', 'sba': 'Ngambay', 'sbb': 'Simbo', 'sbc': 'Kele (Papua New Guinea)', 'sbd': 'Southern Samo', 'sbe': 'Saliba', 'sbf': 'Chabu', 'sbg': 'Seget', 'sbh': 'Sori-Harengan', 'sbi': 'Seti', 'sbj': 'Surbakhal', 'sbk': 'Safwa', 'sbl': 'Botolan Sambal', 'sbm': 'Sagala', 'sbn': 'Sindhi Bhil', 'sbo': 'Sabüm', 'sbp': 'Sangu (Tanzania)', 'sbq': 'Sileibi', 'sbr': 'Sembakung Murut', 'sbs': 'Subiya', 'sbt': 'Kimki', 'sbu': 'Stod Bhoti', 'sbv': 'Sabine', 'sbw': 'Simba', 'sbx': 'Seberuang', 'sby': 'Soli', 'sbz': 'Sara Kaba', 'scb': 'Chut', 'sce': 'Dongxiang', 'scf': 'San Miguel Creole French', 'scg': 'Sanggau', 'sch': 'Sakachep', 'sci': 'Sri Lankan Creole Malay', 'sck': 'Sadri', 'scl': 'Shina', 'scn': 'Sicilian', 'sco': 'Scots', 'scp': 'Helambu Sherpa', 'scq': "Sa'och", 'scs': 'North Slavey', 'scu': 'Shumcho', 'scv': 'Sheni', 'scw': 'Sha', 'scx': 'Sicel', 'sda': "Toraja-Sa'dan", 'sdb': 'Shabak', 'sdc': 'Sassarese Sardinian', 'sde': 'Surubu', 'sdf': 'Sarli', 'sdg': 'Savi', 'sdh': 'Southern Kurdish', 'sdj': 'Suundi', 'sdk': 'Sos Kundi', 'sdl': 'Saudi Arabian Sign Language', 'sdm': 'Semandang', 'sdn': 'Gallurese Sardinian', 'sdo': 'Bukar-Sadung Bidayuh', 'sdp': 'Sherdukpen', 'sdr': 'Oraon Sadri', 'sds': 'Sened', 'sdt': 'Shuadit', 'sdu': 'Sarudu', 'sdx': 'Sibu Melanau', 'sdz': 'Sallands', 'sea': 'Semai', 'seb': 'Shempire Senoufo', 'sec': 'Sechelt', 'sed': 'Sedang', 'see': 'Seneca', 'sef': 'Cebaara Senoufo', 'seg': 'Segeju', 'seh': 'Sena', 'sei': 'Seri', 'sej': 'Sene', 'sek': 'Sekani', 'sel': 'Selkup', 'sen': 'Nanerigé Sénoufo', 'seo': 'Suarmin', 'sep': 'Sìcìté Sénoufo', 'seq': 'Senara Sénoufo', 'ser': 'Serrano', 'ses': 'Koyraboro Senni Songhai', 'set': 'Sentani', 'seu': 'Serui-Laut', 'sev': 'Nyarafolo Senoufo', 'sew': 'Sewa Bay', 'sey': 'Secoya', 'sez': 'Senthang Chin', 'sfb': 'Langue des signes de Belgique Francophone', 'sfe': 'Eastern Subanen', 'sfm': 'Small Flowery Miao', 'sfs': 'South African Sign Language', 'sfw': 'Sehwi', 'sga': 'Old Irish (to 900)', 'sgb': 'Mag-antsi Ayta', 'sgc': 'Kipsigis', 'sgd': 'Surigaonon', 'sge': 'Segai', 'sgg': 'Swiss-German Sign Language', 'sgh': 'Shughni', 'sgi': 'Suga', 'sgj': 'Surgujia', 'sgk': 'Sangkong', 'sgm': 'Singa', 'sgp': 'Singpho', 'sgr': 'Sangisari', 'sgs': 'Samogitian', 'sgt': 'Brokpake', 'sgu': 'Salas', 'sgw': 'Sebat Bet Gurage', 'sgx': 'Sierra Leone Sign Language', 'sgy': 'Sanglechi', 'sgz': 'Sursurunga', 'sha': 'Shall-Zwall', 'shb': 'Ninam', 'shc': 'Sonde', 'shd': 'Kundal Shahi', 'she': 'Sheko', 'shg': 'Shua', 'shh': 'Shoshoni', 'shi': 'Tachelhit', 'shj': 'Shatt', 'shk': 'Shilluk', 'shl': 'Shendu', 'shm': 'Shahrudi', 'shn': 'Shan', 'sho': 'Shanga', 'shp': 'Shipibo-Conibo', 'shq': 'Sala', 'shr': 'Shi', 'shs': 'Shuswap', 'sht': 'Shasta', 'shu': 'Chadian Arabic', 'shv': 'Shehri', 'shw': 'Shwai', 'shx': 'She', 'shy': 'Tachawit', 'shz': 'Syenara Senoufo', 'sia': 'Akkala Sami', 'sib': 'Sebop', 'sid': 'Sidamo', 'sie': 'Simaa', 'sif': 'Siamou', 'sig': 'Paasaal', 'sih': 'Zire', 'sii': 'Shom Peng', 'sij': 'Numbami', 'sik': 'Sikiana', 'sil': 'Tumulung Sisaala', 'sim': 'Mende (Papua New Guinea)', 'sin': 'Sinhala', 'sip': 'Sikkimese', 'siq': 'Sonia', 'sir': 'Siri', 'sis': 'Siuslaw', 'siu': 'Sinagen', 'siv': 'Sumariup', 'siw': 'Siwai', 'six': 'Sumau', 'siy': 'Sivandi', 'siz': 'Siwi', 'sja': 'Epena', 'sjb': 'Sajau Basap', 'sjd': 'Kildin Sami', 'sje': 'Pite Sami', 'sjg': 'Assangori', 'sjk': 'Kemi Sami', 'sjl': 'Sajalong', 'sjm': 'Mapun', 'sjn': 'Sindarin', 'sjo': 'Xibe', 'sjp': 'Surjapuri', 'sjr': 'Siar-Lak', 'sjs': 'Senhaja De Srair', 'sjt': 'Ter Sami', 'sju': 'Ume Sami', 'sjw': 'Shawnee', 'ska': 'Skagit', 'skb': 'Saek', 'skc': 'Ma Manda', 'skd': 'Southern Sierra Miwok', 'ske': 'Seke (Vanuatu)', 'skf': 'Sakirabiá', 'skg': 'Sakalava Malagasy', 'skh': 'Sikule', 'ski': 'Sika', 'skj': 'Seke (Nepal)', 'skk': 'Sok', 'skm': 'Kutong', 'skn': 'Kolibugan Subanon', 'sko': 'Seko Tengah', 'skp': 'Sekapan', 'skq': 'Sininkere', 'skr': 'Saraiki', 'sks': 'Maia', 'skt': 'Sakata', 'sku': 'Sakao', 'skv': 'Skou', 'skw': 'Skepi Creole Dutch', 'skx': 'Seko Padang', 'sky': 'Sikaiana', 'skz': 'Sekar', 'slc': 'Sáliba', 'sld': 'Sissala', 'sle': 'Sholaga', 'slf': 'Swiss-Italian Sign Language', 'slg': 'Selungai Murut', 'slh': 'Southern Puget Sound Salish', 'sli': 'Lower Silesian', 'slj': 'Salumá', 'slk': 'Slovak', 'sll': 'Salt-Yui', 'slm': 'Pangutaran Sama', 'sln': 'Salinan', 'slp': 'Lamaholot', 'slq': 'Salchuq', 'slr': 'Salar', 'sls': 'Singapore Sign Language', 'slt': 'Sila', 'slu': 'Selaru', 'slv': 'Slovenian', 'slw': 'Sialum', 'slx': 'Salampasu', 'sly': 'Selayar', 'slz': "Ma'ya", 'sma': 'Southern Sami', 'smb': 'Simbari', 'smc': 'Som', 'smd': 'Sama', 'sme': 'Northern Sami', 'smf': 'Auwe', 'smg': 'Simbali', 'smh': 'Samei', 'smj': 'Lule Sami', 'smk': 'Bolinao', 'sml': 'Central Sama', 'smm': 'Musasa', 'smn': 'Inari Sami', 'smo': 'Samoan', 'smp': 'Samaritan', 'smq': 'Samo', 'smr': 'Simeulue', 'sms': 'Skolt Sami', 'smt': 'Simte', 'smu': 'Somray', 'smv': 'Samvedi', 'smw': 'Sumbawa', 'smx': 'Samba', 'smy': 'Semnani', 'smz': 'Simeku', 'sna': 'Shona', 'snb': 'Sebuyau', 'snc': 'Sinaugoro', 'snd': 'Sindhi', 'sne': 'Bau Bidayuh', 'snf': 'Noon', 'sng': 'Sanga (Democratic Republic of Congo)', 'snh': 'Shinabo', 'sni': 'Sensi', 'snj': 'Riverain Sango', 'snk': 'Soninke', 'snl': 'Sangil', 'snm': "Southern Ma'di", 'snn': 'Siona', 'sno': 'Snohomish', 'snp': 'Siane', 'snq': 'Sangu (Gabon)', 'snr': 'Sihan', 'sns': 'South West Bay', 'snu': 'Senggi', 'snv': "Sa'ban", 'snw': 'Selee', 'snx': 'Sam', 'sny': 'Saniyo-Hiyewe', 'snz': 'Sinsauru', 'soa': 'Thai Song', 'sob': 'Sobei', 'soc': 'So (Democratic Republic of Congo)', 'sod': 'Songoora', 'soe': 'Songomeno', 'sog': 'Sogdian', 'soh': 'Aka', 'soi': 'Sonha', 'soj': 'Soi', 'sok': 'Sokoro', 'sol': 'Solos', 'som': 'Somali', 'soo': 'Songo', 'sop': 'Songe', 'soq': 'Kanasi', 'sor': 'Somrai', 'sos': 'Seeku', 'sot': 'Southern Sotho', 'sou': 'Southern Thai', 'sov': 'Sonsorol', 'sow': 'Sowanda', 'sox': 'Swo', 'soy': 'Miyobe', 'soz': 'Temi', 'spa': 'Spanish', 'spb': 'Sepa (Indonesia)', 'spc': 'Sapé', 'spd': 'Saep', 'spe': 'Sepa (Papua New Guinea)', 'spg': 'Sian', 'spi': 'Saponi', 'spk': 'Sengo', 'spl': 'Selepet', 'spm': 'Akukem', 'spn': 'Sanapaná', 'spo': 'Spokane', 'spp': 'Supyire Senoufo', 'spq': 'Loreto-Ucayali Spanish', 'spr': 'Saparua', 'sps': 'Saposa', 'spt': 'Spiti Bhoti', 'spu': 'Sapuan', 'spv': 'Sambalpuri', 'spx': 'South Picene', 'spy': 'Sabaot', 'sqa': 'Shama-Sambuga', 'sqh': 'Shau', 'sqi': 'Albanian', 'sqk': 'Albanian Sign Language', 'sqm': 'Suma', 'sqn': 'Susquehannock', 'sqo': 'Sorkhei', 'sqq': 'Sou', 'sqr': 'Siculo Arabic', 'sqs': 'Sri Lankan Sign Language', 'sqt': 'Soqotri', 'squ': 'Squamish', 'sra': 'Saruga', 'srb': 'Sora', 'src': 'Logudorese Sardinian', 'srd': 'Sardinian', 'sre': 'Sara', 'srf': 'Nafi', 'srg': 'Sulod', 'srh': 'Sarikoli', 'sri': 'Siriano', 'srk': 'Serudung Murut', 'srl': 'Isirawa', 'srm': 'Saramaccan', 'srn': 'Sranan Tongo', 'sro': 'Campidanese Sardinian', 'srp': 'Serbian', 'srq': 'Sirionó', 'srr': 'Serer', 'srs': 'Sarsi', 'srt': 'Sauri', 'sru': 'Suruí', 'srv': 'Southern Sorsoganon', 'srw': 'Serua', 'srx': 'Sirmauri', 'sry': 'Sera', 'srz': 'Shahmirzadi', 'ssb': 'Southern Sama', 'ssc': 'Suba-Simbiti', 'ssd': 'Siroi', 'sse': 'Balangingi', 'ssf': 'Thao', 'ssg': 'Seimat', 'ssh': 'Shihhi Arabic', 'ssi': 'Sansi', 'ssj': 'Sausi', 'ssk': 'Sunam', 'ssl': 'Western Sisaala', 'ssm': 'Semnam', 'ssn': 'Waata', 'sso': 'Sissano', 'ssp': 'Spanish Sign Language', 'ssq': "So'a", 'ssr': 'Swiss-French Sign Language', 'sss': 'Sô', 'sst': 'Sinasina', 'ssu': 'Susuami', 'ssv': 'Shark Bay', 'ssw': 'Swati', 'ssx': 'Samberigi', 'ssy': 'Saho', 'ssz': 'Sengseng', 'sta': 'Settla', 'stb': 'Northern Subanen', 'std': 'Sentinel', 'ste': 'Liana-Seti', 'stf': 'Seta', 'stg': 'Trieng', 'sth': 'Shelta', 'sti': 'Bulo Stieng', 'stj': 'Matya Samo', 'stk': 'Arammba', 'stl': 'Stellingwerfs', 'stm': 'Setaman', 'stn': 'Owa', 'sto': 'Stoney', 'stp': 'Southeastern Tepehuan', 'stq': 'Saterfriesisch', 'str': 'Straits Salish', 'sts': 'Shumashti', 'stt': 'Budeh Stieng', 'stu': 'Samtao', 'stv': "Silt'e", 'stw': 'Satawalese', 'sty': 'Siberian Tatar', 'sua': 'Sulka', 'sub': 'Suku', 'suc': 'Western Subanon', 'sue': 'Suena', 'sug': 'Suganga', 'sui': 'Suki', 'suj': 'Shubi', 'suk': 'Sukuma', 'sun': 'Sundanese', 'suq': 'Suri', 'sur': 'Mwaghavul', 'sus': 'Susu', 'sut': 'Subtiaba', 'suv': 'Puroik', 'suw': 'Sumbwa', 'sux': 'Sumerian', 'suy': 'Suyá', 'suz': 'Sunwar', 'sva': 'Svan', 'svb': 'Ulau-Suain', 'svc': 'Vincentian Creole English', 'sve': 'Serili', 'svk': 'Slovakian Sign Language', 'svm': 'Slavomolisano', 'svs': 'Savosavo', 'svx': 'Skalvian', 'swa': 'Swahili (macrolanguage)', 'swb': 'Maore Comorian', 'swc': 'Congo Swahili', 'swe': 'Swedish', 'swf': 'Sere', 'swg': 'Swabian', 'swh': 'Swahili (individual language)', 'swi': 'Sui', 'swj': 'Sira', 'swk': 'Malawi Sena', 'swl': 'Swedish Sign Language', 'swm': 'Samosa', 'swn': 'Sawknah', 'swo': 'Shanenawa', 'swp': 'Suau', 'swq': 'Sharwa', 'swr': 'Saweru', 'sws': 'Seluwasan', 'swt': 'Sawila', 'swu': 'Suwawa', 'swv': 'Shekhawati', 'sww': 'Sowa', 'swx': 'Suruahá', 'swy': 'Sarua', 'sxb': 'Suba', 'sxc': 'Sicanian', 'sxe': 'Sighu', 'sxg': 'Shixing', 'sxk': 'Southern Kalapuya', 'sxl': 'Selian', 'sxm': 'Samre', 'sxn': 'Sangir', 'sxo': 'Sorothaptic', 'sxr': 'Saaroa', 'sxs': 'Sasaru', 'sxu': 'Upper Saxon', 'sxw': 'Saxwe Gbe', 'sya': 'Siang', 'syb': 'Central Subanen', 'syc': 'Classical Syriac', 'syi': 'Seki', 'syk': 'Sukur', 'syl': 'Sylheti', 'sym': 'Maya Samo', 'syn': 'Senaya', 'syo': 'Suoy', 'syr': 'Syriac', 'sys': 'Sinyar', 'syw': 'Kagate', 'syx': 'Samay', 'syy': 'Al-Sayyid Bedouin Sign Language', 'sza': 'Semelai', 'szb': 'Ngalum', 'szc': 'Semaq Beri', 'szd': 'Seru', 'sze': 'Seze', 'szg': 'Sengele', 'szl': 'Silesian', 'szn': 'Sula', 'szp': 'Suabo', 'szv': 'Isu (Fako Division)', 'szw': 'Sawai', 'taa': 'Lower Tanana', 'tab': 'Tabassaran', 'tac': 'Lowland Tarahumara', 'tad': 'Tause', 'tae': 'Tariana', 'taf': 'Tapirapé', 'tag': 'Tagoi', 'tah': 'Tahitian', 'taj': 'Eastern Tamang', 'tak': 'Tala', 'tal': 'Tal', 'tam': 'Tamil', 'tan': 'Tangale', 'tao': 'Yami', 'tap': 'Taabwa', 'taq': 'Tamasheq', 'tar': 'Central Tarahumara', 'tas': 'Tay Boi', 'tat': 'Tatar', 'tau': 'Upper Tanana', 'tav': 'Tatuyo', 'taw': 'Tai', 'tax': 'Tamki', 'tay': 'Atayal', 'taz': 'Tocho', 'tba': 'Aikanã', 'tbb': 'Tapeba', 'tbc': 'Takia', 'tbd': 'Kaki Ae', 'tbe': 'Tanimbili', 'tbf': 'Mandara', 'tbg': 'North Tairora', 'tbh': 'Thurawal', 'tbi': 'Gaam', 'tbj': 'Tiang', 'tbk': 'Calamian Tagbanwa', 'tbl': 'Tboli', 'tbm': 'Tagbu', 'tbn': 'Barro Negro Tunebo', 'tbo': 'Tawala', 'tbp': 'Taworta', 'tbr': 'Tumtum', 'tbs': 'Tanguat', 'tbt': 'Tembo (Kitembo)', 'tbu': 'Tubar', 'tbv': 'Tobo', 'tbw': 'Tagbanwa', 'tbx': 'Kapin', 'tby': 'Tabaru', 'tbz': 'Ditammari', 'tca': 'Ticuna', 'tcb': 'Tanacross', 'tcc': 'Datooga', 'tcd': 'Tafi', 'tce': 'Southern Tutchone', 'tcf': "Malinaltepec Me'phaa", 'tcg': 'Tamagario', 'tch': 'Turks And Caicos Creole English', 'tci': 'Wára', 'tck': 'Tchitchege', 'tcl': 'Taman (Myanmar)', 'tcm': 'Tanahmerah', 'tcn': 'Tichurong', 'tco': 'Taungyo', 'tcp': 'Tawr Chin', 'tcq': 'Kaiy', 'tcs': 'Torres Strait Creole', 'tct': "T'en", 'tcu': 'Southeastern Tarahumara', 'tcw': 'Tecpatlán Totonac', 'tcx': 'Toda', 'tcy': 'Tulu', 'tcz': 'Thado Chin', 'tda': 'Tagdal', 'tdb': 'Panchpargania', 'tdc': 'Emberá-Tadó', 'tdd': 'Tai Nüa', 'tde': 'Tiranige Diga Dogon', 'tdf': 'Talieng', 'tdg': 'Western Tamang', 'tdh': 'Thulung', 'tdi': 'Tomadino', 'tdj': 'Tajio', 'tdk': 'Tambas', 'tdl': 'Sur', 'tdm': 'Taruma', 'tdn': 'Tondano', 'tdo': 'Teme', 'tdq': 'Tita', 'tdr': 'Todrah', 'tds': 'Doutai', 'tdt': 'Tetun Dili', 'tdv': 'Toro', 'tdx': 'Tandroy-Mahafaly Malagasy', 'tdy': 'Tadyawan', 'tea': 'Temiar', 'teb': 'Tetete', 'tec': 'Terik', 'ted': 'Tepo Krumen', 'tee': 'Huehuetla Tepehua', 'tef': 'Teressa', 'teg': 'Teke-Tege', 'teh': 'Tehuelche', 'tei': 'Torricelli', 'tek': 'Ibali Teke', 'tel': 'Telugu', 'tem': 'Timne', 'ten': 'Tama (Colombia)', 'teo': 'Teso', 'tep': 'Tepecano', 'teq': 'Temein', 'ter': 'Tereno', 'tes': 'Tengger', 'tet': 'Tetum', 'teu': 'Soo', 'tev': 'Teor', 'tew': 'Tewa (USA)', 'tex': 'Tennet', 'tey': 'Tulishi', 'tfi': 'Tofin Gbe', 'tfn': 'Tanaina', 'tfo': 'Tefaro', 'tfr': 'Teribe', 'tft': 'Ternate', 'tga': 'Sagalla', 'tgb': 'Tobilung', 'tgc': 'Tigak', 'tgd': 'Ciwogai', 'tge': 'Eastern Gorkha Tamang', 'tgf': 'Chalikha', 'tgh': 'Tobagonian Creole English', 'tgi': 'Lawunuia', 'tgj': 'Tagin', 'tgk': 'Tajik', 'tgl': 'Tagalog', 'tgn': 'Tandaganon', 'tgo': 'Sudest', 'tgp': 'Tangoa', 'tgq': 'Tring', 'tgr': 'Tareng', 'tgs': 'Nume', 'tgt': 'Central Tagbanwa', 'tgu': 'Tanggu', 'tgv': 'Tingui-Boto', 'tgw': 'Tagwana Senoufo', 'tgx': 'Tagish', 'tgy': 'Togoyo', 'tgz': 'Tagalaka', 'tha': 'Thai', 'thd': 'Thayore', 'the': 'Chitwania Tharu', 'thf': 'Thangmi', 'thh': 'Northern Tarahumara', 'thi': 'Tai Long', 'thk': 'Tharaka', 'thl': 'Dangaura Tharu', 'thm': 'Aheu', 'thn': 'Thachanadan', 'thp': 'Thompson', 'thq': 'Kochila Tharu', 'thr': 'Rana Tharu', 'ths': 'Thakali', 'tht': 'Tahltan', 'thu': 'Thuri', 'thv': 'Tahaggart Tamahaq', 'thw': 'Thudam', 'thy': 'Tha', 'thz': 'Tayart Tamajeq', 'tia': 'Tidikelt Tamazight', 'tic': 'Tira', 'tif': 'Tifal', 'tig': 'Tigre', 'tih': 'Timugon Murut', 'tii': 'Tiene', 'tij': 'Tilung', 'tik': 'Tikar', 'til': 'Tillamook', 'tim': 'Timbe', 'tin': 'Tindi', 'tio': 'Teop', 'tip': 'Trimuris', 'tiq': 'Tiéfo', 'tir': 'Tigrinya', 'tis': 'Masadiit Itneg', 'tit': 'Tinigua', 'tiu': 'Adasen', 'tiv': 'Tiv', 'tiw': 'Tiwi', 'tix': 'Southern Tiwa', 'tiy': 'Tiruray', 'tiz': 'Tai Hongjin', 'tja': 'Tajuasohn', 'tjg': 'Tunjung', 'tji': 'Northern Tujia', 'tjl': 'Tai Laing', 'tjm': 'Timucua', 'tjn': 'Tonjon', 'tjo': 'Temacine Tamazight', 'tjs': 'Southern Tujia', 'tju': 'Tjurruru', 'tjw': 'Djabwurrung', 'tka': 'Truká', 'tkb': 'Buksa', 'tkd': 'Tukudede', 'tke': 'Takwane', 'tkf': 'Tukumanféd', 'tkg': 'Tesaka Malagasy', 'tkl': 'Tokelau', 'tkm': 'Takelma', 'tkn': 'Toku-No-Shima', 'tkp': 'Tikopia', 'tkq': 'Tee', 'tkr': 'Tsakhur', 'tks': 'Takestani', 'tkt': 'Kathoriya Tharu', 'tku': 'Upper Necaxa Totonac', 'tkv': 'Mur Pano', 'tkw': 'Teanu', 'tkx': 'Tangko', 'tkz': 'Takua', 'tla': 'Southwestern Tepehuan', 'tlb': 'Tobelo', 'tlc': 'Yecuatla Totonac', 'tld': 'Talaud', 'tlf': 'Telefol', 'tlg': 'Tofanma', 'tlh': 'Klingon', 'tli': 'Tlingit', 'tlj': 'Talinga-Bwisi', 'tlk': 'Taloki', 'tll': 'Tetela', 'tlm': 'Tolomako', 'tln': "Talondo'", 'tlo': 'Talodi', 'tlp': 'Filomena Mata-Coahuitlán Totonac', 'tlq': 'Tai Loi', 'tlr': 'Talise', 'tls': 'Tambotalo', 'tlt': 'Sou Nama', 'tlu': 'Tulehu', 'tlv': 'Taliabu', 'tlx': 'Khehek', 'tly': 'Talysh', 'tma': 'Tama (Chad)', 'tmb': 'Katbol', 'tmc': 'Tumak', 'tmd': 'Haruai', 'tme': 'Tremembé', 'tmf': 'Toba-Maskoy', 'tmg': 'Ternateño', 'tmh': 'Tamashek', 'tmi': 'Tutuba', 'tmj': 'Samarokena', 'tmk': 'Northwestern Tamang', 'tml': 'Tamnim Citak', 'tmm': 'Tai Thanh', 'tmn': 'Taman (Indonesia)', 'tmo': 'Temoq', 'tmq': 'Tumleo', 'tmr': 'Jewish Babylonian Aramaic (ca. 200-1200 CE)', 'tms': 'Tima', 'tmt': 'Tasmate', 'tmu': 'Iau', 'tmv': 'Tembo (Motembo)', 'tmw': 'Temuan', 'tmy': 'Tami', 'tmz': 'Tamanaku', 'tna': 'Tacana', 'tnb': 'Western Tunebo', 'tnc': 'Tanimuca-Retuarã', 'tnd': 'Angosturas Tunebo', 'tne': 'Tinoc Kallahan', 'tng': 'Tobanga', 'tnh': 'Maiani', 'tni': 'Tandia', 'tnk': 'Kwamera', 'tnl': 'Lenakel', 'tnm': 'Tabla', 'tnn': 'North Tanna', 'tno': 'Toromono', 'tnp': 'Whitesands', 'tnq': 'Taino', 'tnr': 'Ménik', 'tns': 'Tenis', 'tnt': 'Tontemboan', 'tnu': 'Tay Khang', 'tnv': 'Tangchangya', 'tnw': 'Tonsawang', 'tnx': 'Tanema', 'tny': 'Tongwe', 'tnz': "Ten'edn", 'tob': 'Toba', 'toc': 'Coyutla Totonac', 'tod': 'Toma', 'tof': 'Gizrra', 'tog': 'Tonga (Nyasa)', 'toh': 'Gitonga', 'toi': 'Tonga (Zambia)', 'toj': 'Tojolabal', 'tol': 'Tolowa', 'tom': 'Tombulu', 'ton': 'Tonga (Tonga Islands)', 'too': 'Xicotepec De Juárez Totonac', 'top': 'Papantla Totonac', 'toq': 'Toposa', 'tor': 'Togbo-Vara Banda', 'tos': 'Highland Totonac', 'tou': 'Tho', 'tov': 'Upper Taromi', 'tow': 'Jemez', 'tox': 'Tobian', 'toy': 'Topoiyo', 'toz': 'To', 'tpa': 'Taupota', 'tpc': "Azoyú Me'phaa", 'tpe': 'Tippera', 'tpf': 'Tarpia', 'tpg': 'Kula', 'tpi': 'Tok Pisin', 'tpj': 'Tapieté', 'tpk': 'Tupinikin', 'tpl': "Tlacoapa Me'phaa", 'tpm': 'Tampulma', 'tpn': 'Tupinambá', 'tpo': 'Tai Pao', 'tpp': 'Pisaflores Tepehua', 'tpq': 'Tukpa', 'tpr': 'Tuparí', 'tpt': 'Tlachichilco Tepehua', 'tpu': 'Tampuan', 'tpv': 'Tanapag', 'tpw': 'Tupí', 'tpx': "Acatepec Me'phaa", 'tpy': 'Trumai', 'tpz': 'Tinputz', 'tqb': 'Tembé', 'tql': 'Lehali', 'tqm': 'Turumsa', 'tqn': 'Tenino', 'tqo': 'Toaripi', 'tqp': 'Tomoip', 'tqq': 'Tunni', 'tqr': 'Torona', 'tqt': 'Western Totonac', 'tqu': 'Touo', 'tqw': 'Tonkawa', 'tra': 'Tirahi', 'trb': 'Terebu', 'trc': 'Copala Triqui', 'trd': 'Turi', 'tre': 'East Tarangan', 'trf': 'Trinidadian Creole English', 'trg': 'Lishán Didán', 'trh': 'Turaka', 'tri': 'Trió', 'trj': 'Toram', 'trl': 'Traveller Scottish', 'trm': 'Tregami', 'trn': 'Trinitario', 'tro': 'Tarao Naga', 'trp': 'Kok Borok', 'trq': 'San Martín Itunyoso Triqui', 'trr': 'Taushiro', 'trs': 'Chicahuaxtla Triqui', 'trt': 'Tunggare', 'tru': 'Turoyo', 'trv': 'Taroko', 'trw': 'Torwali', 'trx': 'Tringgus-Sembaan Bidayuh', 'try': 'Turung', 'trz': 'Torá', 'tsa': 'Tsaangi', 'tsb': 'Tsamai', 'tsc': 'Tswa', 'tsd': 'Tsakonian', 'tse': 'Tunisian Sign Language', 'tsg': 'Tausug', 'tsh': 'Tsuvan', 'tsi': 'Tsimshian', 'tsj': 'Tshangla', 'tsk': 'Tseku', 'tsl': "Ts'ün-Lao", 'tsm': 'Turkish Sign Language', 'tsn': 'Tswana', 'tso': 'Tsonga', 'tsp': 'Northern Toussian', 'tsq': 'Thai Sign Language', 'tsr': 'Akei', 'tss': 'Taiwan Sign Language', 'tst': 'Tondi Songway Kiini', 'tsu': 'Tsou', 'tsv': 'Tsogo', 'tsw': 'Tsishingini', 'tsx': 'Mubami', 'tsy': 'Tebul Sign Language', 'tsz': 'Purepecha', 'tta': 'Tutelo', 'ttb': 'Gaa', 'ttc': 'Tektiteko', 'ttd': 'Tauade', 'tte': 'Bwanabwana', 'ttf': 'Tuotomb', 'ttg': 'Tutong', 'tth': "Upper Ta'oih", 'tti': 'Tobati', 'ttj': 'Tooro', 'ttk': 'Totoro', 'ttl': 'Totela', 'ttm': 'Northern Tutchone', 'ttn': 'Towei', 'tto': "Lower Ta'oih", 'ttp': 'Tombelala', 'ttq': 'Tawallammat Tamajaq', 'ttr': 'Tera', 'tts': 'Northeastern Thai', 'ttt': 'Muslim Tat', 'ttu': 'Torau', 'ttv': 'Titan', 'ttw': 'Long Wat', 'tty': 'Sikaritai', 'ttz': 'Tsum', 'tua': 'Wiarumus', 'tub': 'Tübatulabal', 'tuc': 'Mutu', 'tud': 'Tuxá', 'tue': 'Tuyuca', 'tuf': 'Central Tunebo', 'tug': 'Tunia', 'tuh': 'Taulil', 'tui': 'Tupuri', 'tuj': 'Tugutil', 'tuk': 'Turkmen', 'tul': 'Tula', 'tum': 'Tumbuka', 'tun': 'Tunica', 'tuo': 'Tucano', 'tuq': 'Tedaga', 'tur': 'Turkish', 'tus': 'Tuscarora', 'tuu': 'Tututni', 'tuv': 'Turkana', 'tux': 'Tuxináwa', 'tuy': 'Tugen', 'tuz': 'Turka', 'tva': 'Vaghua', 'tvd': 'Tsuvadi', 'tve': "Te'un", 'tvk': 'Southeast Ambrym', 'tvl': 'Tuvalu', 'tvm': 'Tela-Masbuar', 'tvn': 'Tavoyan', 'tvo': 'Tidore', 'tvs': 'Taveta', 'tvt': 'Tutsa Naga', 'tvu': 'Tunen', 'tvw': 'Sedoa', 'tvy': 'Timor Pidgin', 'twa': 'Twana', 'twb': 'Western Tawbuid', 'twc': 'Teshenawa', 'twd': 'Twents', 'twe': 'Tewa (Indonesia)', 'twf': 'Northern Tiwa', 'twg': 'Tereweng', 'twh': 'Tai Dón', 'twi': 'Twi', 'twl': 'Tawara', 'twm': 'Tawang Monpa', 'twn': 'Twendi', 'two': 'Tswapong', 'twp': 'Ere', 'twq': 'Tasawaq', 'twr': 'Southwestern Tarahumara', 'twt': 'Turiwára', 'twu': 'Termanu', 'tww': 'Tuwari', 'twx': 'Tewe', 'twy': 'Tawoyan', 'txa': 'Tombonuo', 'txb': 'Tokharian B', 'txc': 'Tsetsaut', 'txe': 'Totoli', 'txg': 'Tangut', 'txh': 'Thracian', 'txi': 'Ikpeng', 'txj': 'Tarjumo', 'txm': 'Tomini', 'txn': 'West Tarangan', 'txo': 'Toto', 'txq': 'Tii', 'txr': 'Tartessian', 'txs': 'Tonsea', 'txt': 'Citak', 'txu': 'Kayapó', 'txx': 'Tatana', 'txy': 'Tanosy Malagasy', 'tya': 'Tauya', 'tye': 'Kyanga', 'tyh': "O'du", 'tyi': 'Teke-Tsaayi', 'tyj': 'Tai Do', 'tyl': 'Thu Lao', 'tyn': 'Kombai', 'typ': 'Thaypan', 'tyr': 'Tai Daeng', 'tys': 'Tày Sa Pa', 'tyt': 'Tày Tac', 'tyu': 'Kua', 'tyv': 'Tuvinian', 'tyx': 'Teke-Tyee', 'tyz': 'Tày', 'tza': 'Tanzanian Sign Language', 'tzh': 'Tzeltal', 'tzj': "Tz'utujil", 'tzl': 'Talossan', 'tzm': 'Central Atlas Tamazight', 'tzn': 'Tugun', 'tzo': 'Tzotzil', 'tzx': 'Tabriak', 'uam': 'Uamué', 'uan': 'Kuan', 'uar': 'Tairuma', 'uba': 'Ubang', 'ubi': 'Ubi', 'ubl': "Buhi'non Bikol", 'ubr': 'Ubir', 'ubu': 'Umbu-Ungu', 'uby': 'Ubykh', 'uda': 'Uda', 'ude': 'Udihe', 'udg': 'Muduga', 'udi': 'Udi', 'udj': 'Ujir', 'udl': 'Wuzlam', 'udm': 'Udmurt', 'udu': 'Uduk', 'ues': 'Kioko', 'ufi': 'Ufim', 'uga': 'Ugaritic', 'ugb': 'Kuku-Ugbanh', 'uge': 'Ughele', 'ugn': 'Ugandan Sign Language', 'ugo': 'Ugong', 'ugy': 'Uruguayan Sign Language', 'uha': 'Uhami', 'uhn': 'Damal', 'uig': 'Uighur', 'uis': 'Uisai', 'uiv': 'Iyive', 'uji': 'Tanjijili', 'uka': 'Kaburi', 'ukg': 'Ukuriguma', 'ukh': 'Ukhwejo', 'ukl': 'Ukrainian Sign Language', 'ukp': 'Ukpe-Bayobiri', 'ukq': 'Ukwa', 'ukr': 'Ukrainian', 'uks': 'Urubú-Kaapor Sign Language', 'uku': 'Ukue', 'ukw': 'Ukwuani-Aboh-Ndoni', 'uky': 'Kuuk-Yak', 'ula': 'Fungwa', 'ulb': 'Ulukwumi', 'ulc': 'Ulch', 'ule': 'Lule', 'ulf': 'Usku', 'uli': 'Ulithian', 'ulk': 'Meriam', 'ull': 'Ullatan', 'ulm': "Ulumanda'", 'uln': 'Unserdeutsch', 'ulu': "Uma' Lung", 'ulw': 'Ulwa', 'uma': 'Umatilla', 'umb': 'Umbundu', 'umc': 'Marrucinian', 'umd': 'Umbindhamu', 'umg': 'Umbuygamu', 'umi': 'Ukit', 'umm': 'Umon', 'umn': 'Makyan Naga', 'umo': 'Umotína', 'ump': 'Umpila', 'umr': 'Umbugarla', 'ums': 'Pendau', 'umu': 'Munsee', 'una': 'North Watut', 'und': 'Undetermined', 'une': 'Uneme', 'ung': 'Ngarinyin', 'unk': 'Enawené-Nawé', 'unm': 'Unami', 'unn': 'Kurnai', 'unr': 'Mundari', 'unu': 'Unubahe', 'unx': 'Munda', 'unz': 'Unde Kaili', 'upi': 'Umeda', 'upv': 'Uripiv-Wala-Rano-Atchin', 'ura': 'Urarina', 'urb': 'Urubú-Kaapor', 'urc': 'Urningangg', 'urd': 'Urdu', 'ure': 'Uru', 'urf': 'Uradhi', 'urg': 'Urigina', 'urh': 'Urhobo', 'uri': 'Urim', 'urk': "Urak Lawoi'", 'url': 'Urali', 'urm': 'Urapmin', 'urn': 'Uruangnirin', 'uro': 'Ura (Papua New Guinea)', 'urp': 'Uru-Pa-In', 'urr': 'Lehalurup', 'urt': 'Urat', 'uru': 'Urumi', 'urv': 'Uruava', 'urw': 'Sop', 'urx': 'Urimo', 'ury': 'Orya', 'urz': 'Uru-Eu-Wau-Wau', 'usa': 'Usarufa', 'ush': 'Ushojo', 'usi': 'Usui', 'usk': 'Usaghade', 'usp': 'Uspanteco', 'usu': 'Uya', 'uta': 'Otank', 'ute': 'Ute-Southern Paiute', 'utp': 'Amba (Solomon Islands)', 'utr': 'Etulo', 'utu': 'Utu', 'uum': 'Urum', 'uun': 'Kulon-Pazeh', 'uur': 'Ura (Vanuatu)', 'uuu': 'U', 'uve': 'West Uvean', 'uvh': 'Uri', 'uvl': 'Lote', 'uwa': 'Kuku-Uwanh', 'uya': 'Doko-Uyanga', 'uzb': 'Uzbek', 'uzn': 'Northern Uzbek', 'uzs': 'Southern Uzbek', 'vaa': 'Vaagri Booli', 'vae': 'Vale', 'vaf': 'Vafsi', 'vag': 'Vagla', 'vah': 'Varhadi-Nagpuri', 'vai': 'Vai', 'vaj': 'Sekele', 'val': 'Vehes', 'vam': 'Vanimo', 'van': 'Valman', 'vao': 'Vao', 'vap': 'Vaiphei', 'var': 'Huarijio', 'vas': 'Vasavi', 'vau': 'Vanuma', 'vav': 'Varli', 'vay': 'Wayu', 'vbb': 'Southeast Babar', 'vbk': 'Southwestern Bontok', 'vec': 'Venetian', 'ved': 'Veddah', 'vel': 'Veluws', 'vem': 'Vemgo-Mabas', 'ven': 'Venda', 'veo': 'Ventureño', 'vep': 'Veps', 'ver': 'Mom Jango', 'vgr': 'Vaghri', 'vgt': 'Vlaamse Gebarentaal', 'vic': 'Virgin Islands Creole English', 'vid': 'Vidunda', 'vie': 'Vietnamese', 'vif': 'Vili', 'vig': 'Viemo', 'vil': 'Vilela', 'vin': 'Vinza', 'vis': 'Vishavan', 'vit': 'Viti', 'viv': 'Iduna', 'vka': 'Kariyarra', 'vki': 'Ija-Zuba', 'vkj': 'Kujarge', 'vkk': 'Kaur', 'vkl': 'Kulisusu', 'vkm': 'Kamakan', 'vko': 'Kodeoha', 'vkp': 'Korlai Creole Portuguese', 'vkt': 'Tenggarong Kutai Malay', 'vku': 'Kurrama', 'vlp': 'Valpei', 'vls': 'Vlaams', 'vma': 'Martuyhunira', 'vmb': 'Barbaram', 'vmc': 'Juxtlahuaca Mixtec', 'vmd': 'Mudu Koraga', 'vme': 'East Masela', 'vmf': 'Mainfränkisch', 'vmg': 'Lungalunga', 'vmh': 'Maraghei', 'vmi': 'Miwa', 'vmj': 'Ixtayutla Mixtec', 'vmk': 'Makhuwa-Shirima', 'vml': 'Malgana', 'vmm': 'Mitlatongo Mixtec', 'vmp': 'Soyaltepec Mazatec', 'vmq': 'Soyaltepec Mixtec', 'vmr': 'Marenje', 'vms': 'Moksela', 'vmu': 'Muluridyi', 'vmv': 'Valley Maidu', 'vmw': 'Makhuwa', 'vmx': 'Tamazola Mixtec', 'vmy': 'Ayautla Mazatec', 'vmz': 'Mazatlán Mazatec', 'vnk': 'Vano', 'vnm': 'Vinmavis', 'vnp': 'Vunapu', 'vol': 'Volapük', 'vor': 'Voro', 'vot': 'Votic', 'vra': "Vera'a", 'vro': 'Võro', 'vrs': 'Varisi', 'vrt': 'Burmbar', 'vsi': 'Moldova Sign Language', 'vsl': 'Venezuelan Sign Language', 'vsv': 'Valencian Sign Language', 'vto': 'Vitou', 'vum': 'Vumbu', 'vun': 'Vunjo', 'vut': 'Vute', 'vwa': 'Awa (China)', 'waa': 'Walla Walla', 'wab': 'Wab', 'wac': 'Wasco-Wishram', 'wad': 'Wandamen', 'wae': 'Walser', 'waf': 'Wakoná', 'wag': "Wa'ema", 'wah': 'Watubela', 'wai': 'Wares', 'waj': 'Waffa', 'wal': 'Wolaytta', 'wam': 'Wampanoag', 'wan': 'Wan', 'wao': 'Wappo', 'wap': 'Wapishana', 'waq': 'Wageman', 'war': 'Waray (Philippines)', 'was': 'Washo', 'wat': 'Kaninuwa', 'wau': 'Waurá', 'wav': 'Waka', 'waw': 'Waiwai', 'wax': 'Watam', 'way': 'Wayana', 'waz': 'Wampur', 'wba': 'Warao', 'wbb': 'Wabo', 'wbe': 'Waritai', 'wbf': 'Wara', 'wbh': 'Wanda', 'wbi': 'Vwanji', 'wbj': 'Alagwa', 'wbk': 'Waigali', 'wbl': 'Wakhi', 'wbm': 'Wa', 'wbp': 'Warlpiri', 'wbq': 'Waddar', 'wbr': 'Wagdi', 'wbt': 'Wanman', 'wbv': 'Wajarri', 'wbw': 'Woi', 'wca': 'Yanomámi', 'wci': 'Waci Gbe', 'wdd': 'Wandji', 'wdg': 'Wadaginam', 'wdj': 'Wadjiginy', 'wdk': 'Wadikali', 'wdu': 'Wadjigu', 'wdy': 'Wadjabangayi', 'wea': 'Wewaw', 'wec': 'Wè Western', 'wed': 'Wedau', 'weg': 'Wergaia', 'weh': 'Weh', 'wei': 'Kiunum', 'wem': 'Weme Gbe', 'weo': 'Wemale', 'wep': 'Westphalien', 'wer': 'Weri', 'wes': 'Cameroon Pidgin', 'wet': 'Perai', 'weu': 'Rawngtu Chin', 'wew': 'Wejewa', 'wfg': 'Yafi', 'wga': 'Wagaya', 'wgb': 'Wagawaga', 'wgg': 'Wangganguru', 'wgi': 'Wahgi', 'wgo': 'Waigeo', 'wgu': 'Wirangu', 'wgy': 'Warrgamay', 'wha': 'Sou Upaa', 'whg': 'North Wahgi', 'whk': 'Wahau Kenyah', 'whu': 'Wahau Kayan', 'wib': 'Southern Toussian', 'wic': 'Wichita', 'wie': 'Wik-Epa', 'wif': 'Wik-Keyangan', 'wig': 'Wik-Ngathana', 'wih': "Wik-Me'anha", 'wii': 'Minidien', 'wij': 'Wik-Iiyanh', 'wik': 'Wikalkan', 'wil': 'Wilawila', 'wim': 'Wik-Mungkan', 'win': 'Ho-Chunk', 'wir': 'Wiraféd', 'wiu': 'Wiru', 'wiv': 'Vitu', 'wiy': 'Wiyot', 'wja': 'Waja', 'wji': 'Warji', 'wka': "Kw'adza", 'wkb': 'Kumbaran', 'wkd': 'Wakde', 'wkl': 'Kalanadi', 'wku': 'Kunduvadi', 'wkw': 'Wakawaka', 'wky': 'Wangkayutyuru', 'wla': 'Walio', 'wlc': 'Mwali Comorian', 'wle': 'Wolane', 'wlg': 'Kunbarlang', 'wli': 'Waioli', 'wlk': 'Wailaki', 'wll': 'Wali (Sudan)', 'wlm': 'Middle Welsh', 'wln': 'Walloon', 'wlo': 'Wolio', 'wlr': 'Wailapa', 'wls': 'Wallisian', 'wlu': 'Wuliwuli', 'wlv': 'Wichí Lhamtés Vejoz', 'wlw': 'Walak', 'wlx': 'Wali (Ghana)', 'wly': 'Waling', 'wma': 'Mawa (Nigeria)', 'wmb': 'Wambaya', 'wmc': 'Wamas', 'wmd': 'Mamaindé', 'wme': 'Wambule', 'wmh': "Waima'a", 'wmi': 'Wamin', 'wmm': 'Maiwa (Indonesia)', 'wmn': 'Waamwang', 'wmo': 'Wom (Papua New Guinea)', 'wms': 'Wambon', 'wmt': 'Walmajarri', 'wmw': 'Mwani', 'wmx': 'Womo', 'wnb': 'Wanambre', 'wnc': 'Wantoat', 'wnd': 'Wandarang', 'wne': 'Waneci', 'wng': 'Wanggom', 'wni': 'Ndzwani Comorian', 'wnk': 'Wanukaka', 'wnm': 'Wanggamala', 'wnn': 'Wunumara', 'wno': 'Wano', 'wnp': 'Wanap', 'wnu': 'Usan', 'wnw': 'Wintu', 'wny': 'Wanyi', 'woa': 'Tyaraity', 'wob': 'Wè Northern', 'woc': 'Wogeo', 'wod': 'Wolani', 'woe': 'Woleaian', 'wof': 'Gambian Wolof', 'wog': 'Wogamusin', 'woi': 'Kamang', 'wok': 'Longto', 'wol': 'Wolof', 'wom': 'Wom (Nigeria)', 'won': 'Wongo', 'woo': 'Manombai', 'wor': 'Woria', 'wos': 'Hanga Hundi', 'wow': 'Wawonii', 'woy': 'Weyto', 'wpc': 'Maco', 'wra': 'Warapu', 'wrb': 'Warluwara', 'wrd': 'Warduji', 'wrg': 'Warungu', 'wrh': 'Wiradhuri', 'wri': 'Wariyangga', 'wrk': 'Garrwa', 'wrl': 'Warlmanpa', 'wrm': 'Warumungu', 'wrn': 'Warnang', 'wro': 'Worrorra', 'wrp': 'Waropen', 'wrr': 'Wardaman', 'wrs': 'Waris', 'wru': 'Waru', 'wrv': 'Waruna', 'wrw': 'Gugu Warra', 'wrx': 'Wae Rana', 'wry': 'Merwari', 'wrz': 'Waray (Australia)', 'wsa': 'Warembori', 'wsg': 'Adilabad Gondi', 'wsi': 'Wusi', 'wsk': 'Waskia', 'wsr': 'Owenia', 'wss': 'Wasa', 'wsu': 'Wasu', 'wsv': 'Wotapuri-Katarqalai', 'wtf': 'Watiwa', 'wth': 'Wathawurrung', 'wti': 'Berta', 'wtk': 'Watakataui', 'wtm': 'Mewati', 'wtw': 'Wotu', 'wua': 'Wikngenchera', 'wub': 'Wunambal', 'wud': 'Wudu', 'wuh': 'Wutunhua', 'wul': 'Silimo', 'wum': 'Wumbvu', 'wun': 'Bungu', 'wur': 'Wurrugu', 'wut': 'Wutung', 'wuu': 'Wu Chinese', 'wuv': 'Wuvulu-Aua', 'wux': 'Wulna', 'wuy': 'Wauyai', 'wwa': 'Waama', 'wwb': 'Wakabunga', 'wwo': 'Wetamut', 'wwr': 'Warrwa', 'www': 'Wawa', 'wxa': 'Waxianghua', 'wxw': 'Wardandi', 'wya': 'Wyandot', 'wyb': 'Wangaaybuwan-Ngiyambaa', 'wyi': 'Woiwurrung', 'wym': 'Wymysorys', 'wyr': 'Wayoró', 'wyy': 'Western Fijian', 'xaa': 'Andalusian Arabic', 'xab': 'Sambe', 'xac': 'Kachari', 'xad': 'Adai', 'xae': 'Aequian', 'xag': 'Aghwan', 'xai': 'Kaimbé', 'xaj': 'Ararandewára', 'xak': 'Máku', 'xal': 'Kalmyk', 'xam': '/Xam', 'xan': 'Xamtanga', 'xao': 'Khao', 'xap': 'Apalachee', 'xaq': 'Aquitanian', 'xar': 'Karami', 'xas': 'Kamas', 'xat': 'Katawixi', 'xau': 'Kauwera', 'xav': 'Xavánte', 'xaw': 'Kawaiisu', 'xay': 'Kayan Mahakam', 'xbb': 'Lower Burdekin', 'xbc': 'Bactrian', 'xbd': 'Bindal', 'xbe': 'Bigambal', 'xbg': 'Bunganditj', 'xbi': 'Kombio', 'xbj': 'Birrpayi', 'xbm': 'Middle Breton', 'xbn': 'Kenaboi', 'xbo': 'Bolgarian', 'xbp': 'Bibbulman', 'xbr': 'Kambera', 'xbw': 'Kambiwá', 'xby': 'Batyala', 'xcb': 'Cumbric', 'xcc': 'Camunic', 'xce': 'Celtiberian', 'xcg': 'Cisalpine Gaulish', 'xch': 'Chemakum', 'xcl': 'Classical Armenian', 'xcm': 'Comecrudo', 'xcn': 'Cotoname', 'xco': 'Chorasmian', 'xcr': 'Carian', 'xct': 'Classical Tibetan', 'xcu': 'Curonian', 'xcv': 'Chuvantsy', 'xcw': 'Coahuilteco', 'xcy': 'Cayuse', 'xda': 'Darkinyung', 'xdc': 'Dacian', 'xdk': 'Dharuk', 'xdm': 'Edomite', 'xdy': 'Malayic Dayak', 'xeb': 'Eblan', 'xed': 'Hdi', 'xeg': '//Xegwi', 'xel': 'Kelo', 'xem': 'Kembayan', 'xep': 'Epi-Olmec', 'xer': 'Xerénte', 'xes': 'Kesawai', 'xet': 'Xetá', 'xeu': 'Keoru-Ahia', 'xfa': 'Faliscan', 'xga': 'Galatian', 'xgb': 'Gbin', 'xgd': 'Gudang', 'xgf': 'Gabrielino-Fernandeño', 'xgg': 'Goreng', 'xgi': 'Garingbal', 'xgl': 'Galindan', 'xgm': 'Dharumbal', 'xgr': 'Garza', 'xgu': 'Unggumi', 'xgw': 'Guwa', 'xha': 'Harami', 'xhc': 'Hunnic', 'xhd': 'Hadrami', 'xhe': 'Khetrani', 'xho': 'Xhosa', 'xhr': 'Hernican', 'xht': 'Hattic', 'xhu': 'Hurrian', 'xhv': 'Khua', 'xib': 'Iberian', 'xii': 'Xiri', 'xil': 'Illyrian', 'xin': 'Xinca', 'xir': 'Xiriâna', 'xis': 'Kisan', 'xiv': 'Indus Valley Language', 'xiy': 'Xipaya', 'xjb': 'Minjungbal', 'xjt': 'Jaitmatang', 'xka': 'Kalkoti', 'xkb': 'Northern Nago', 'xkc': "Kho'ini", 'xkd': 'Mendalam Kayan', 'xke': 'Kereho', 'xkf': 'Khengkha', 'xkg': 'Kagoro', 'xki': 'Kenyan Sign Language', 'xkj': 'Kajali', 'xkk': "Kaco'", 'xkl': 'Mainstream Kenyah', 'xkn': 'Kayan River Kayan', 'xko': 'Kiorr', 'xkp': 'Kabatei', 'xkq': 'Koroni', 'xkr': 'Xakriabá', 'xks': 'Kumbewaha', 'xkt': 'Kantosi', 'xku': 'Kaamba', 'xkv': 'Kgalagadi', 'xkw': 'Kembra', 'xkx': 'Karore', 'xky': "Uma' Lasan", 'xkz': 'Kurtokha', 'xla': 'Kamula', 'xlb': 'Loup B', 'xlc': 'Lycian', 'xld': 'Lydian', 'xle': 'Lemnian', 'xlg': 'Ligurian (Ancient)', 'xli': 'Liburnian', 'xln': 'Alanic', 'xlo': 'Loup A', 'xlp': 'Lepontic', 'xls': 'Lusitanian', 'xlu': 'Cuneiform Luwian', 'xly': 'Elymian', 'xma': 'Mushungulu', 'xmb': 'Mbonga', 'xmc': 'Makhuwa-Marrevone', 'xmd': 'Mbudum', 'xme': 'Median', 'xmf': 'Mingrelian', 'xmg': 'Mengaka', 'xmh': 'Kuku-Muminh', 'xmj': 'Majera', 'xmk': 'Ancient Macedonian', 'xml': 'Malaysian Sign Language', 'xmm': 'Manado Malay', 'xmn': 'Manichaean Middle Persian', 'xmo': 'Morerebi', 'xmp': "Kuku-Mu'inh", 'xmq': 'Kuku-Mangk', 'xmr': 'Meroitic', 'xms': 'Moroccan Sign Language', 'xmt': 'Matbat', 'xmu': 'Kamu', 'xmv': 'Antankarana Malagasy', 'xmw': 'Tsimihety Malagasy', 'xmx': 'Maden', 'xmy': 'Mayaguduna', 'xmz': 'Mori Bawah', 'xna': 'Ancient North Arabian', 'xnb': 'Kanakanabu', 'xng': 'Middle Mongolian', 'xnh': 'Kuanhua', 'xni': 'Ngarigu', 'xnk': 'Nganakarti', 'xnn': 'Northern Kankanay', 'xno': 'Anglo-Norman', 'xnr': 'Kangri', 'xns': 'Kanashi', 'xnt': 'Narragansett', 'xnu': 'Nukunul', 'xny': 'Nyiyaparli', 'xnz': 'Kenzi', 'xoc': "O'chi'chi'", 'xod': 'Kokoda', 'xog': 'Soga', 'xoi': 'Kominimung', 'xok': 'Xokleng', 'xom': 'Komo (Sudan)', 'xon': 'Konkomba', 'xoo': 'Xukurú', 'xop': 'Kopar', 'xor': 'Korubo', 'xow': 'Kowaki', 'xpa': 'Pirriya', 'xpc': 'Pecheneg', 'xpe': 'Liberia Kpelle', 'xpg': 'Phrygian', 'xpi': 'Pictish', 'xpj': 'Mpalitjanh', 'xpk': 'Kulina Pano', 'xpm': 'Pumpokol', 'xpn': 'Kapinawá', 'xpo': 'Pochutec', 'xpp': 'Puyo-Paekche', 'xpq': 'Mohegan-Pequot', 'xpr': 'Parthian', 'xps': 'Pisidian', 'xpt': 'Punthamara', 'xpu': 'Punic', 'xpy': 'Puyo', 'xqa': 'Karakhanid', 'xqt': 'Qatabanian', 'xra': 'Krahô', 'xrb': 'Eastern Karaboro', 'xrd': 'Gundungurra', 'xre': 'Kreye', 'xrg': 'Minang', 'xri': 'Krikati-Timbira', 'xrm': 'Armazic', 'xrn': 'Arin', 'xrq': 'Karranga', 'xrr': 'Raetic', 'xrt': 'Aranama-Tamique', 'xru': 'Marriammu', 'xrw': 'Karawa', 'xsa': 'Sabaean', 'xsb': 'Sambal', 'xsc': 'Scythian', 'xsd': 'Sidetic', 'xse': 'Sempan', 'xsh': 'Shamang', 'xsi': 'Sio', 'xsl': 'South Slavey', 'xsm': 'Kasem', 'xsn': 'Sanga (Nigeria)', 'xso': 'Solano', 'xsp': 'Silopi', 'xsq': 'Makhuwa-Saka', 'xsr': 'Sherpa', 'xss': 'Assan', 'xsu': 'Sanumá', 'xsv': 'Sudovian', 'xsy': 'Saisiyat', 'xta': 'Alcozauca Mixtec', 'xtb': 'Chazumba Mixtec', 'xtc': 'Katcha-Kadugli-Miri', 'xtd': 'Diuxi-Tilantongo Mixtec', 'xte': 'Ketengban', 'xtg': 'Transalpine Gaulish', 'xth': 'Yitha Yitha', 'xti': 'Sinicahua Mixtec', 'xtj': 'San Juan Teita Mixtec', 'xtl': 'Tijaltepec Mixtec', 'xtm': 'Magdalena Peñasco Mixtec', 'xtn': 'Northern Tlaxiaco Mixtec', 'xto': 'Tokharian A', 'xtp': 'San Miguel Piedras Mixtec', 'xtq': 'Tumshuqese', 'xtr': 'Early Tripuri', 'xts': 'Sindihui Mixtec', 'xtt': 'Tacahua Mixtec', 'xtu': 'Cuyamecalco Mixtec', 'xtv': 'Thawa', 'xtw': 'Tawandê', 'xty': 'Yoloxochitl Mixtec', 'xtz': 'Tasmanian', 'xua': 'Alu Kurumba', 'xub': 'Betta Kurumba', 'xud': 'Umiida', 'xug': 'Kunigami', 'xuj': 'Jennu Kurumba', 'xul': 'Ngunawal', 'xum': 'Umbrian', 'xun': 'Unggaranggu', 'xuo': 'Kuo', 'xup': 'Upper Umpqua', 'xur': 'Urartian', 'xut': 'Kuthant', 'xuu': 'Kxoe', 'xve': 'Venetic', 'xvi': 'Kamviri', 'xvn': 'Vandalic', 'xvo': 'Volscian', 'xvs': 'Vestinian', 'xwa': 'Kwaza', 'xwc': 'Woccon', 'xwd': 'Wadi Wadi', 'xwe': 'Xwela Gbe', 'xwg': 'Kwegu', 'xwj': 'Wajuk', 'xwk': 'Wangkumara', 'xwl': 'Western Xwla Gbe', 'xwo': 'Written Oirat', 'xwr': 'Kwerba Mamberamo', 'xwt': 'Wotjobaluk', 'xww': 'Wemba Wemba', 'xxb': 'Boro (Ghana)', 'xxk': "Ke'o", 'xxm': 'Minkin', 'xxr': 'Koropó', 'xxt': 'Tambora', 'xya': 'Yaygir', 'xyb': 'Yandjibara', 'xyj': 'Mayi-Yapi', 'xyk': 'Mayi-Kulan', 'xyl': 'Yalakalore', 'xyt': 'Mayi-Thakurti', 'xyy': 'Yorta Yorta', 'xzh': 'Zhang-Zhung', 'xzm': 'Zemgalian', 'xzp': 'Ancient Zapotec', 'yaa': 'Yaminahua', 'yab': 'Yuhup', 'yac': 'Pass Valley Yali', 'yad': 'Yagua', 'yae': 'Pumé', 'yaf': 'Yaka (Democratic Republic of Congo)', 'yag': 'Yámana', 'yah': 'Yazgulyam', 'yai': 'Yagnobi', 'yaj': 'Banda-Yangere', 'yak': 'Yakama', 'yal': 'Yalunka', 'yam': 'Yamba', 'yan': 'Mayangna', 'yao': 'Yao', 'yap': 'Yapese', 'yaq': 'Yaqui', 'yar': 'Yabarana', 'yas': 'Nugunu (Cameroon)', 'yat': 'Yambeta', 'yau': 'Yuwana', 'yav': 'Yangben', 'yaw': 'Yawalapití', 'yax': 'Yauma', 'yay': 'Agwagwune', 'yaz': 'Lokaa', 'yba': 'Yala', 'ybb': 'Yemba', 'ybe': 'West Yugur', 'ybh': 'Yakha', 'ybi': 'Yamphu', 'ybj': 'Hasha', 'ybk': 'Bokha', 'ybl': 'Yukuben', 'ybm': 'Yaben', 'ybn': 'Yabaâna', 'ybo': 'Yabong', 'ybx': 'Yawiyo', 'yby': 'Yaweyuha', 'ych': 'Chesu', 'ycl': 'Lolopo', 'ycn': 'Yucuna', 'ycp': 'Chepya', 'yda': 'Yanda', 'ydd': 'Eastern Yiddish', 'yde': 'Yangum Dey', 'ydg': 'Yidgha', 'ydk': 'Yoidik', 'yea': 'Ravula', 'yec': 'Yeniche', 'yee': 'Yimas', 'yei': 'Yeni', 'yej': 'Yevanic', 'yel': 'Yela', 'yer': 'Tarok', 'yes': 'Nyankpa', 'yet': 'Yetfa', 'yeu': 'Yerukula', 'yev': 'Yapunda', 'yey': 'Yeyi', 'yga': 'Malyangapa', 'ygi': 'Yiningayi', 'ygl': 'Yangum Gel', 'ygm': 'Yagomi', 'ygp': 'Gepo', 'ygr': 'Yagaria', 'ygs': 'Yolŋu Sign Language', 'ygu': 'Yugul', 'ygw': 'Yagwoia', 'yha': 'Baha Buyang', 'yhd': 'Judeo-Iraqi Arabic', 'yhl': 'Hlepho Phowa', 'yhs': 'Yan-nhaŋu Sign Language', 'yia': 'Yinggarda', 'yid': 'Yiddish', 'yif': 'Ache', 'yig': 'Wusa Nasu', 'yih': 'Western Yiddish', 'yii': 'Yidiny', 'yij': 'Yindjibarndi', 'yik': 'Dongshanba Lalo', 'yil': 'Yindjilandji', 'yim': 'Yimchungru Naga', 'yin': 'Yinchia', 'yip': 'Pholo', 'yiq': 'Miqie', 'yir': 'North Awyu', 'yis': 'Yis', 'yit': 'Eastern Lalu', 'yiu': 'Awu', 'yiv': 'Northern Nisu', 'yix': 'Axi Yi', 'yiz': 'Azhe', 'yka': 'Yakan', 'ykg': 'Northern Yukaghir', 'yki': 'Yoke', 'ykk': 'Yakaikeke', 'ykl': 'Khlula', 'ykm': 'Kap', 'ykn': 'Kua-nsi', 'yko': 'Yasa', 'ykr': 'Yekora', 'ykt': 'Kathu', 'yku': 'Kuamasi', 'yky': 'Yakoma', 'yla': 'Yaul', 'ylb': 'Yaleba', 'yle': 'Yele', 'ylg': 'Yelogu', 'yli': 'Angguruk Yali', 'yll': 'Yil', 'ylm': 'Limi', 'yln': 'Langnian Buyang', 'ylo': 'Naluo Yi', 'ylr': 'Yalarnnga', 'ylu': 'Aribwaung', 'yly': 'Nyâlayu', 'ymb': 'Yambes', 'ymc': 'Southern Muji', 'ymd': 'Muda', 'yme': 'Yameo', 'ymg': 'Yamongeri', 'ymh': 'Mili', 'ymi': 'Moji', 'ymk': 'Makwe', 'yml': 'Iamalele', 'ymm': 'Maay', 'ymn': 'Yamna', 'ymo': 'Yangum Mon', 'ymp': 'Yamap', 'ymq': 'Qila Muji', 'ymr': 'Malasar', 'yms': 'Mysian', 'ymx': 'Northern Muji', 'ymz': 'Muzi', 'yna': 'Aluo', 'ynd': 'Yandruwandha', 'yne': "Lang'e", 'yng': 'Yango', 'ynk': 'Naukan Yupik', 'ynl': 'Yangulam', 'ynn': 'Yana', 'yno': 'Yong', 'ynq': 'Yendang', 'yns': 'Yansi', 'ynu': 'Yahuna', 'yob': 'Yoba', 'yog': 'Yogad', 'yoi': 'Yonaguni', 'yok': 'Yokuts', 'yol': 'Yola', 'yom': 'Yombe', 'yon': 'Yongkom', 'yor': 'Yoruba', 'yot': 'Yotti', 'yox': 'Yoron', 'yoy': 'Yoy', 'ypa': 'Phala', 'ypb': 'Labo Phowa', 'ypg': 'Phola', 'yph': 'Phupha', 'ypm': 'Phuma', 'ypn': 'Ani Phowa', 'ypo': 'Alo Phola', 'ypp': 'Phupa', 'ypz': 'Phuza', 'yra': 'Yerakai', 'yrb': 'Yareba', 'yre': 'Yaouré', 'yrk': 'Nenets', 'yrl': 'Nhengatu', 'yrm': 'Yirrk-Mel', 'yrn': 'Yerong', 'yro': 'Yaroamë', 'yrs': 'Yarsun', 'yrw': 'Yarawata', 'yry': 'Yarluyandi', 'ysc': 'Yassic', 'ysd': 'Samatao', 'ysg': 'Sonaga', 'ysl': 'Yugoslavian Sign Language', 'ysn': 'Sani', 'yso': 'Nisi (China)', 'ysp': 'Southern Lolopo', 'ysr': 'Sirenik Yupik', 'yss': 'Yessan-Mayo', 'ysy': 'Sanie', 'yta': 'Talu', 'ytl': 'Tanglang', 'ytp': 'Thopho', 'ytw': 'Yout Wam', 'yty': 'Yatay', 'yua': 'Yucateco', 'yub': 'Yugambal', 'yuc': 'Yuchi', 'yud': 'Judeo-Tripolitanian Arabic', 'yue': 'Yue Chinese', 'yuf': 'Havasupai-Walapai-Yavapai', 'yug': 'Yug', 'yui': 'Yurutí', 'yuj': 'Karkar-Yuri', 'yuk': 'Yuki', 'yul': 'Yulu', 'yum': 'Quechan', 'yun': 'Bena (Nigeria)', 'yup': 'Yukpa', 'yuq': 'Yuqui', 'yur': 'Yurok', 'yut': 'Yopno', 'yuw': 'Yau (Morobe Province)', 'yux': 'Southern Yukaghir', 'yuy': 'East Yugur', 'yuz': 'Yuracare', 'yva': 'Yawa', 'yvt': 'Yavitero', 'ywa': 'Kalou', 'ywg': 'Yinhawangka', 'ywl': 'Western Lalu', 'ywn': 'Yawanawa', 'ywq': 'Wuding-Luquan Yi', 'ywr': 'Yawuru', 'ywt': 'Xishanba Lalo', 'ywu': 'Wumeng Nasu', 'yww': 'Yawarawarga', 'yxa': 'Mayawali', 'yxg': 'Yagara', 'yxl': 'Yardliyawarra', 'yxm': 'Yinwum', 'yxu': 'Yuyu', 'yxy': 'Yabula Yabula', 'yyr': 'Yir Yoront', 'yyu': 'Yau (Sandaun Province)', 'yyz': 'Ayizi', 'yzg': "E'ma Buyang", 'yzk': 'Zokhuo', 'zaa': 'Sierra de Juárez Zapotec', 'zab': 'Western Tlacolula Valley Zapotec', 'zac': 'Ocotlán Zapotec', 'zad': 'Cajonos Zapotec', 'zae': 'Yareni Zapotec', 'zaf': 'Ayoquesco Zapotec', 'zag': 'Zaghawa', 'zah': 'Zangwal', 'zai': 'Isthmus Zapotec', 'zaj': 'Zaramo', 'zak': 'Zanaki', 'zal': 'Zauzou', 'zam': 'Miahuatlán Zapotec', 'zao': 'Ozolotepec Zapotec', 'zap': 'Zapotec', 'zaq': 'Aloápam Zapotec', 'zar': 'Rincón Zapotec', 'zas': 'Santo Domingo Albarradas Zapotec', 'zat': 'Tabaa Zapotec', 'zau': 'Zangskari', 'zav': 'Yatzachi Zapotec', 'zaw': 'Mitla Zapotec', 'zax': 'Xadani Zapotec', 'zay': 'Zayse-Zergulla', 'zaz': 'Zari', 'zbc': 'Central Berawan', 'zbe': 'East Berawan', 'zbl': 'Blissymbols', 'zbt': 'Batui', 'zbw': 'West Berawan', 'zca': 'Coatecas Altas Zapotec', 'zch': 'Central Hongshuihe Zhuang', 'zdj': 'Ngazidja Comorian', 'zea': 'Zeeuws', 'zeg': 'Zenag', 'zeh': 'Eastern Hongshuihe Zhuang', 'zen': 'Zenaga', 'zga': 'Kinga', 'zgb': 'Guibei Zhuang', 'zgh': 'Standard Moroccan Tamazight', 'zgm': 'Minz Zhuang', 'zgn': 'Guibian Zhuang', 'zgr': 'Magori', 'zha': 'Zhuang', 'zhb': 'Zhaba', 'zhd': 'Dai Zhuang', 'zhi': 'Zhire', 'zhn': 'Nong Zhuang', 'zho': 'Chinese', 'zhw': 'Zhoa', 'zia': 'Zia', 'zib': 'Zimbabwe Sign Language', 'zik': 'Zimakani', 'zil': 'Zialo', 'zim': 'Mesme', 'zin': 'Zinza', 'zir': 'Ziriya', 'ziw': 'Zigula', 'ziz': 'Zizilivakan', 'zka': 'Kaimbulawa', 'zkb': 'Koibal', 'zkd': 'Kadu', 'zkg': 'Koguryo', 'zkh': 'Khorezmian', 'zkk': 'Karankawa', 'zkn': 'Kanan', 'zko': 'Kott', 'zkp': 'São Paulo Kaingáng', 'zkr': 'Zakhring', 'zkt': 'Kitan', 'zku': 'Kaurna', 'zkv': 'Krevinian', 'zkz': 'Khazar', 'zlj': 'Liujiang Zhuang', 'zlm': 'Malay (individual language)', 'zln': 'Lianshan Zhuang', 'zlq': 'Liuqian Zhuang', 'zma': 'Manda (Australia)', 'zmb': 'Zimba', 'zmc': 'Margany', 'zmd': 'Maridan', 'zme': 'Mangerr', 'zmf': 'Mfinu', 'zmg': 'Marti Ke', 'zmh': 'Makolkol', 'zmi': 'Negeri Sembilan Malay', 'zmj': 'Maridjabin', 'zmk': 'Mandandanyi', 'zml': 'Madngele', 'zmm': 'Marimanindji', 'zmn': 'Mbangwe', 'zmo': 'Molo', 'zmp': 'Mpuono', 'zmq': 'Mituku', 'zmr': 'Maranunggu', 'zms': 'Mbesa', 'zmt': 'Maringarr', 'zmu': 'Muruwari', 'zmv': 'Mbariman-Gudhinma', 'zmw': 'Mbo (Democratic Republic of Congo)', 'zmx': 'Bomitaba', 'zmy': 'Mariyedi', 'zmz': 'Mbandja', 'zna': 'Zan Gula', 'zne': 'Zande (individual language)', 'zng': 'Mang', 'znk': 'Manangkari', 'zns': 'Mangas', 'zoc': 'Copainalá Zoque', 'zoh': 'Chimalapa Zoque', 'zom': 'Zou', 'zoo': 'Asunción Mixtepec Zapotec', 'zoq': 'Tabasco Zoque', 'zor': 'Rayón Zoque', 'zos': 'Francisco León Zoque', 'zpa': 'Lachiguiri Zapotec', 'zpb': 'Yautepec Zapotec', 'zpc': 'Choapan Zapotec', 'zpd': 'Southeastern Ixtlán Zapotec', 'zpe': 'Petapa Zapotec', 'zpf': 'San Pedro Quiatoni Zapotec', 'zpg': 'Guevea De Humboldt Zapotec', 'zph': 'Totomachapan Zapotec', 'zpi': 'Santa María Quiegolani Zapotec', 'zpj': 'Quiavicuzas Zapotec', 'zpk': 'Tlacolulita Zapotec', 'zpl': 'Lachixío Zapotec', 'zpm': 'Mixtepec Zapotec', 'zpn': 'Santa Inés Yatzechi Zapotec', 'zpo': 'Amatlán Zapotec', 'zpp': 'El Alto Zapotec', 'zpq': 'Zoogocho Zapotec', 'zpr': 'Santiago Xanica Zapotec', 'zps': 'Coatlán Zapotec', 'zpt': 'San Vicente Coatlán Zapotec', 'zpu': 'Yalálag Zapotec', 'zpv': 'Chichicapan Zapotec', 'zpw': 'Zaniza Zapotec', 'zpx': 'San Baltazar Loxicha Zapotec', 'zpy': 'Mazaltepec Zapotec', 'zpz': 'Texmelucan Zapotec', 'zqe': 'Qiubei Zhuang', 'zra': 'Kara (Korea)', 'zrg': 'Mirgan', 'zrn': 'Zerenkel', 'zro': 'Záparo', 'zrp': 'Zarphatic', 'zrs': 'Mairasi', 'zsa': 'Sarasira', 'zsk': 'Kaskean', 'zsl': 'Zambian Sign Language', 'zsm': 'Standard Malay', 'zsr': 'Southern Rincon Zapotec', 'zsu': 'Sukurum', 'zte': 'Elotepec Zapotec', 'ztg': 'Xanaguía Zapotec', 'ztl': 'Lapaguía-Guivini Zapotec', 'ztm': 'San Agustín Mixtepec Zapotec', 'ztn': 'Santa Catarina Albarradas Zapotec', 'ztp': 'Loxicha Zapotec', 'ztq': 'Quioquitani-Quierí Zapotec', 'zts': 'Tilquiapan Zapotec', 'ztt': 'Tejalapan Zapotec', 'ztu': 'Güilá Zapotec', 'ztx': 'Zaachila Zapotec', 'zty': 'Yatee Zapotec', 'zua': 'Zeem', 'zuh': 'Tokano', 'zul': 'Zulu', 'zum': 'Kumzari', 'zun': 'Zuni', 'zuy': 'Zumaya', 'zwa': 'Zay', 'zxx': 'No linguistic content', 'zyb': 'Yongbei Zhuang', 'zyg': 'Yang Zhuang', 'zyj': 'Youjiang Zhuang', 'zyn': 'Yongnan Zhuang', 'zyp': 'Zyphe Chin', 'zza': 'Zaza', 'zzj': 'Zuojiang Zhuang' };
var apiRoot = 'https://farm.openzim.org';


/***/ }),

/***/ "./src/app/services/schedules.service.ts":
/*!***********************************************!*\
  !*** ./src/app/services/schedules.service.ts ***!
  \***********************************************/
/*! exports provided: SchedulesService, Beat, BeatConfig, CrontabBeatConfig */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "SchedulesService", function() { return SchedulesService; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "Beat", function() { return Beat; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "BeatConfig", function() { return BeatConfig; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "CrontabBeatConfig", function() { return CrontabBeatConfig; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm5/http.js");
/* harmony import */ var cronstrue__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! cronstrue */ "./node_modules/cronstrue/dist/cronstrue.js");
/* harmony import */ var cronstrue__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(cronstrue__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _const_service__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./const.service */ "./src/app/services/const.service.ts");
/* harmony import */ var rxjs_operators__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! rxjs/operators */ "./node_modules/rxjs/_esm5/operators/index.js");
var __extends = (undefined && undefined.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
        return extendStatics(d, b);
    }
    return function (d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (undefined && undefined.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};





var SchedulesService = /** @class */ (function () {
    function SchedulesService(http) {
        this.http = http;
    }
    SchedulesService.prototype.list = function (skip, limit) {
        if (skip === void 0) { skip = 0; }
        if (limit === void 0) { limit = 20; }
        return this.http.get('https://farm.openzim.org/api/schedules/', {
            params: {
                skip: skip.toString(),
                limit: limit.toString()
            }
        }).pipe(Object(rxjs_operators__WEBPACK_IMPORTED_MODULE_4__["map"])(function (data) {
            for (var _i = 0, _a = data.items; _i < _a.length; _i++) {
                var item = _a[_i];
                item.language = _const_service__WEBPACK_IMPORTED_MODULE_3__["languageNames"][item.language];
                item.beat = new Beat(item.beat.type, item.beat.config);
            }
            return data;
        }));
    };
    SchedulesService = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["Injectable"])({
            providedIn: 'root',
        }),
        __metadata("design:paramtypes", [_angular_common_http__WEBPACK_IMPORTED_MODULE_1__["HttpClient"]])
    ], SchedulesService);
    return SchedulesService;
}());

var Beat = /** @class */ (function () {
    function Beat(type, config) {
        this.type = type;
        this.config = config;
    }
    Beat.prototype.description = function () {
        if (this.type == 'crontab') {
            var minute = this.config['minute'] != null ? this.config['minute'] : '*';
            var hour = this.config['hour'] != null ? this.config['hour'] : '*';
            var day_of_week = this.config['day_of_week'] != null ? this.config['day_of_week'] : '*';
            var day_of_month = this.config['day_of_month'] != null ? this.config['day_of_month'] : '*';
            var month_of_year = this.config['month_of_year'] != null ? this.config['month_of_year'] : '*';
            return cronstrue__WEBPACK_IMPORTED_MODULE_2___default.a.toString(Array(minute, hour, day_of_month, month_of_year, day_of_week).join(' '));
        }
        else {
            return '';
        }
    };
    return Beat;
}());

var BeatConfig = /** @class */ (function () {
    function BeatConfig(config) {
        this.config = config;
    }
    BeatConfig.prototype.updateDescription = function () { };
    return BeatConfig;
}());

var CrontabBeatConfig = /** @class */ (function (_super) {
    __extends(CrontabBeatConfig, _super);
    function CrontabBeatConfig(config) {
        var _this = _super.call(this, config) || this;
        _this.updateDescription();
        return _this;
    }
    Object.defineProperty(CrontabBeatConfig.prototype, "minute", {
        get: function () { return this.getValue('minute'); },
        set: function (value) { this.config['minute'] = value; },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(CrontabBeatConfig.prototype, "hour", {
        get: function () { return this.getValue('hour'); },
        set: function (value) { this.config['hour'] = value; },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(CrontabBeatConfig.prototype, "day_of_week", {
        get: function () { return this.getValue('day_of_week'); },
        set: function (value) { this.config['day_of_week'] = value; },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(CrontabBeatConfig.prototype, "day_of_month", {
        get: function () { return this.getValue('day_of_month'); },
        set: function (value) { this.config['day_of_month'] = value; },
        enumerable: true,
        configurable: true
    });
    Object.defineProperty(CrontabBeatConfig.prototype, "month_of_year", {
        get: function () { return this.getValue('month_of_year'); },
        set: function (value) { this.config['month_of_year'] = value; },
        enumerable: true,
        configurable: true
    });
    CrontabBeatConfig.prototype.getValue = function (name) {
        var value = this.config[name];
        return value != null && value != '' ? this.config[name] : '*';
    };
    CrontabBeatConfig.prototype.updateDescription = function () {
        this.description = cronstrue__WEBPACK_IMPORTED_MODULE_2___default.a.toString(Array(this.minute, this.hour, this.day_of_month, this.month_of_year, this.day_of_week).join(' '));
    };
    return CrontabBeatConfig;
}(BeatConfig));



/***/ }),

/***/ "./src/app/shared/shared.module.ts":
/*!*****************************************!*\
  !*** ./src/app/shared/shared.module.ts ***!
  \*****************************************/
/*! exports provided: SharedModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "SharedModule", function() { return SharedModule; });
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm5/core.js");
/* harmony import */ var _angular_common__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/common */ "./node_modules/@angular/common/fesm5/common.js");
/* harmony import */ var time_ago_pipe__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! time-ago-pipe */ "./node_modules/time-ago-pipe/esm5/time-ago-pipe.js");
var __decorate = (undefined && undefined.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};



var SharedModule = /** @class */ (function () {
    function SharedModule() {
    }
    SharedModule = __decorate([
        Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["NgModule"])({
            imports: [_angular_common__WEBPACK_IMPORTED_MODULE_1__["CommonModule"]],
            declarations: [
                time_ago_pipe__WEBPACK_IMPORTED_MODULE_2__["TimeAgoPipe"]
            ],
            exports: [
                time_ago_pipe__WEBPACK_IMPORTED_MODULE_2__["TimeAgoPipe"]
            ]
        })
    ], SharedModule);
    return SharedModule;
}());



/***/ })

}]);
//# sourceMappingURL=schedule-schedule-module.js.map