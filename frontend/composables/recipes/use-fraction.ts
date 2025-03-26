/* frac.js (C) 2012-present SheetJS -- http://sheetjs.com */
/* https://developer.aliyun.com/mirror/npm/package/frac/v/0.3.0 Apache license */

import { findClosestValue } from "../use-utils";

function frac(x: number, D: number, mixed: boolean) {
  let n1 = Math.floor(x);
  let d1 = 1;
  let n2 = n1 + 1;
  let d2 = 1;
  if (x !== n1)
    while (d1 <= D && d2 <= D) {
      const m = (n1 + n2) / (d1 + d2);
      if (x === m) {
        if (d1 + d2 <= D) {
          d1 += d2;
          n1 += n2;
          d2 = D + 1;
        } else if (d1 > d2) d2 = D + 1;
        else d1 = D + 1;
        break;
      } else if (x < m) {
        n2 = n1 + n2;
        d2 = d1 + d2;
      } else {
        n1 = n1 + n2;
        d1 = d1 + d2;
      }
    }
  if (d1 > D) {
    d1 = d2;
    n1 = n2;
  }
  if (!mixed) return [0, n1, d1];
  const q = Math.floor(n1 / d1);
  return [q, n1 - q * d1, d1];
}
function simpleFrac(x: number, includeThirds: boolean) {
  // Uses only thirds and quarters
  const floor = Math.floor(x);
  if (floor === x) {
    return [floor, 0, 0];
  }

  const rest = x - floor;

  if (!includeThirds) {
    const quarters = Math.round(rest / 0.25);
    if (quarters === 0) {
      return [floor, 0, 0];
    }
    if (quarters === 4) {
      return [floor + 1, 0, 0];
    }
    const fraction = { 1: [1, 4], 2: [1, 2], 3: [3, 4] }[quarters];
    return fraction ? [floor, fraction[0], fraction[1]] : [x, 0, 0];
  }

  const fractions: Array<[number, number[]]> = [[0, [0, 0]], [0.25, [1, 4]], [0.33, [1, 3]], [0.50, [1, 2]], [0.66, [2, 3]], [0.75, [3, 4]], [1, [0, 0]]];
  const fraction = findClosestValue(rest, fractions) as [number, number[]];
  return [floor + (fraction[0] === 1 ? 1 : 0), fraction[1][0], fraction[1][1]];
  // for (let i = 1; i < levels.length; i++) {
  //   if (levels[i][0] > rest) {
  //     if (rest === levels[i - 1][0]) {
  //       return [floor + (levels[i - 1][0] === 1 ? 1 : 0), levels[i - 1][1], levels[i - 1][2]];
  //     } else {
  //       const diffDown = rest - levels[i - 1][0];
  //       const diffUp = levels[i][0] - rest;
  //       const fraction = diffDown < diffUp ? levels[i - 1] : levels[i];
  //       return [floor + (fraction[0] === 1 ? 1 : 0), fraction[1], fraction[2]];
  //     }
  //   }
  // }
  // return [x, 0, 0]
}
function cont(x: number, D: number, mixed: boolean) {
  const sgn = x < 0 ? -1 : 1;
  let B = x * sgn;
  let P_2 = 0;
  let P_1 = 1;
  let P = 0;
  let Q_2 = 1;
  let Q_1 = 0;
  let Q = 0;
  let A = Math.floor(B);
  while (Q_1 < D) {
    A = Math.floor(B);
    P = A * P_1 + P_2;
    Q = A * Q_1 + Q_2;
    if (B - A < 0.00000005) break;
    B = 1 / (B - A);
    P_2 = P_1;
    P_1 = P;
    Q_2 = Q_1;
    Q_1 = Q;
  }
  if (Q > D) {
    if (Q_1 > D) {
      Q = Q_2;
      P = P_2;
    } else {
      Q = Q_1;
      P = P_1;
    }
  }
  if (!mixed) return [0, sgn * P, Q];
  const q = Math.floor((sgn * P) / Q);
  return [q, sgn * P - q * Q, Q];
}

export const useFraction = function () {
  return {
    frac,
    simpleFrac,
    cont,
  };
};
