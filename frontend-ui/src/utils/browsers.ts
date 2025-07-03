export function isFirefoxOnIOS() {
  const ua = navigator.userAgent.toLowerCase();
  return (
    ua.indexOf("mobile") >= 0 &&
    ua.indexOf("mozilla") >= 0 &&
    ua.indexOf("applewebkit") >= 0
  );
}
