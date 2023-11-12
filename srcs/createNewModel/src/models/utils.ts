export const toFloat = (value: string | number): number => {
    return parseFloat(Number(value).toFixed(2))
}