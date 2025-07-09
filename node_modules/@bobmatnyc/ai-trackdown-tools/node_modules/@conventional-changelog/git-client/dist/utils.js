/**
 * Format arguments.
 * @param args
 * @returns Formatted arguments.
 */
export function formatArgs(...args) {
    return args.reduce((finalArgs, arg) => {
        if (arg) {
            finalArgs.push(String(arg));
        }
        return finalArgs;
    }, []);
}
/**
 * Convert value to array.
 * @param value
 * @returns Array.
 */
export function toArray(value) {
    return Array.isArray(value) ? value : [value];
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoidXRpbHMuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi9zcmMvdXRpbHMudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBRUE7Ozs7R0FJRztBQUNILE1BQU0sVUFBVSxVQUFVLENBQUMsR0FBRyxJQUFXO0lBQ3ZDLE9BQU8sSUFBSSxDQUFDLE1BQU0sQ0FBVyxDQUFDLFNBQVMsRUFBRSxHQUFHLEVBQUUsRUFBRTtRQUM5QyxJQUFJLEdBQUcsRUFBRTtZQUNQLFNBQVMsQ0FBQyxJQUFJLENBQUMsTUFBTSxDQUFDLEdBQUcsQ0FBQyxDQUFDLENBQUE7U0FDNUI7UUFFRCxPQUFPLFNBQVMsQ0FBQTtJQUNsQixDQUFDLEVBQUUsRUFBRSxDQUFDLENBQUE7QUFDUixDQUFDO0FBRUQ7Ozs7R0FJRztBQUNILE1BQU0sVUFBVSxPQUFPLENBQUksS0FBYztJQUN2QyxPQUFPLEtBQUssQ0FBQyxPQUFPLENBQUMsS0FBSyxDQUFDLENBQUMsQ0FBQyxDQUFDLEtBQUssQ0FBQyxDQUFDLENBQUMsQ0FBQyxLQUFLLENBQUMsQ0FBQTtBQUMvQyxDQUFDIn0=