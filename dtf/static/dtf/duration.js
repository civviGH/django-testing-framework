
const iso8601DurationRegex = /^(?<sign>[-+]?)P(?:(?<days>\d+(\.\d+)?)D)?(?:T(?:(?<hours>\d+(\.\d+)?)H)?(?:(?<minutes>\d+(\.\d+)?)M)?(?:(?<seconds>\d+(\.\d+)?)S)?)?$/u

function parseISO8601Duration(iso8601DurationStr) {
    var matches = iso8601DurationRegex.exec(iso8601DurationStr);

    return {
        sign: matches.groups.sign === undefined ? '+' : matches.groups.sign,
        days: matches.groups.days === undefined ? 0 : parseFloat(matches.groups.days),
        hours: matches.groups.hours === undefined ? 0 : parseFloat(matches.groups.hours),
        minutes: matches.groups.minutes === undefined ? 0 : parseFloat(matches.groups.minutes),
        seconds: matches.groups.seconds === undefined ? 0 : parseFloat(matches.groups.seconds)
    };
}

function totalSeconds(duration) {
    return (duration.sign === '-' ? -1 : 1) *
        (duration.days*24*60*60 +
        duration.hours*60*60 +
        duration.minutes*60 + 
        duration.seconds);
}

function printISO8601Duration(duration) {

    const hh = String(duration.hours);
    const mm = String(duration.minutes).padStart(2, '0');
    const ss = String(Math.floor(duration.seconds)).padStart(2, '0');

    result = `${hh}:${mm}:${ss}`;

    if(duration.days > 0) {
        plural = (duration.days > 1) ? 's' : '';
        result = `${duration.days} day${plural}` + result;
    }

    let ms = Math.round((duration.seconds % 1) * 1000000);
    if(ms >= 0) {
        ms = String(ms).padStart(6, '0')
        result += `.${ms}`;
    }

    return result;
}
