// Password rules shown on sign-up and reset. The server enforces the same rules
// (backend/app/auth/passwords.py); this copy only gives instant feedback.

export const MIN_PASSWORD_LENGTH = 12;

// Frequently used passwords that pass the length rule. Compared case-insensitively.
const COMMON = new Set([
  "password1234", "password12345", "password123456", "passw0rd1234", "123456789012", "1234567890123",
  "12345678901234", "qwertyuiopas", "qwertyuiop123", "qwerty123456", "1qaz2wsx3edc", "iloveyou1234",
  "letmein12345", "welcome12345", "welcome123456", "administrator", "admin1234567", "abc123456789",
  "abcdefghijkl", "aaaaaaaaaaaa", "111111111111", "000000000000", "trustno11234", "football1234",
  "baseball1234", "superman1234", "sunshine1234", "princess1234", "dragon123456", "monkey123456",
  "changeme1234", "smartlab1234", "smartlabai123", "laboratory123", "laboratory1234", "qazwsxedcrfv",
  "zaq12wsxcde3", "asdfghjkl123", "1234qwerasdf", "p@ssw0rd1234", "password!234", "mypassword123",
]);

/** True when the password is on the common list or is an obvious pattern (one repeated character, a plain sequence). */
export function isCommonPassword(pw, { email = "", name = "" } = {}) {
  const p = String(pw ?? "").toLowerCase();
  if (!p) return false;
  if (COMMON.has(p)) return true;
  if (/^(.)\1+$/.test(p)) return true;
  if ("01234567890123456789".includes(p) || "abcdefghijklmnopqrstuvwxyz".includes(p) || "qwertyuiopasdfghjklzxcvbnm".includes(p)) return true;
  const local = email.toLowerCase().split("@")[0];
  if (local.length >= 4 && p.includes(local)) return true;
  const first = name.toLowerCase().split(/\s+/)[0] ?? "";
  if (first.length >= 4 && p.replace(/[^a-z]/g, "") === first) return true;
  return false;
}

/** Rule checklist + a 0-4 strength score for the meter. */
export function checkPassword(pw, context = {}) {
  const p = String(pw ?? "");
  const longEnough = p.length >= MIN_PASSWORD_LENGTH;
  const notCommon = p.length > 0 && !isCommonPassword(p, context);
  const classes = [/[a-z]/, /[A-Z]/, /\d/, /[^A-Za-z0-9]/].filter((r) => r.test(p)).length;
  let score = 0;
  if (p.length >= 8) score += 1;
  if (longEnough) score += 1;
  if (p.length >= 16 || classes >= 3) score += 1;
  if (longEnough && classes >= 3 && p.length >= 14) score += 1;
  if (!notCommon) score = Math.min(score, 1);
  return {
    valid: longEnough && notCommon,
    score,
    label: ["Too weak", "Weak", "Fair", "Strong", "Very strong"][score],
    rules: [
      { id: "length", label: `At least ${MIN_PASSWORD_LENGTH} characters`, ok: longEnough },
      { id: "common", label: "Not a common or easily guessed password", ok: notCommon },
    ],
    mixed: classes >= 3,
  };
}

export const isEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(v ?? "").trim());
