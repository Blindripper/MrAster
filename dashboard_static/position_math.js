export function derivePositionMarkPrice({
  mark,
  entry,
  quantity,
  notional,
  pnl,
  side,
} = {}) {
  if (Number.isFinite(mark) && Math.abs(mark) > 0) {
    return Math.abs(mark);
  }

  const entryPrice = Number.isFinite(entry) && Math.abs(entry) > 0 ? Math.abs(entry) : null;
  if (!Number.isFinite(entryPrice) || entryPrice <= 0) {
    return null;
  }

  let signedQuantity = Number.isFinite(quantity) && quantity !== 0 ? quantity : null;
  if (!Number.isFinite(signedQuantity) || signedQuantity === 0) {
    const notionalValue = Number.isFinite(notional) && Math.abs(notional) > 0 ? notional : null;
    if (Number.isFinite(notionalValue) && entryPrice > 0) {
      const magnitude = Math.abs(notionalValue) / entryPrice;
      if (Number.isFinite(magnitude) && Math.abs(magnitude) > 0) {
        let direction = null;
        if (side) {
          const normalized = side.toString().toLowerCase();
          if (normalized === 'buy' || normalized === 'long') {
            direction = 1;
          } else if (normalized === 'sell' || normalized === 'short') {
            direction = -1;
          }
        }
        if (direction === null) {
          direction = notionalValue < 0 ? -1 : 1;
        }
        signedQuantity = magnitude * direction;
      }
    }
  }

  const pnlValue = Number.isFinite(pnl) ? pnl : null;
  if (!Number.isFinite(signedQuantity) || signedQuantity === 0 || pnlValue === null) {
    return null;
  }

  const derived = entryPrice + pnlValue / signedQuantity;
  if (!Number.isFinite(derived) || derived <= 0) {
    return null;
  }

  return Math.abs(derived);
}
