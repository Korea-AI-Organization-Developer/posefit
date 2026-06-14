/** 조건부 클래스 결합 — falsy 값은 걸러낸다 */
export function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}
