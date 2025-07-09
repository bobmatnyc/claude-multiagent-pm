import { concatBufferStream } from '@simple-libs/stream-utils';
/**
 * Wait for a child process to exit and return its exit code.
 * @param process
 * @returns A promise that resolves to the exit code of the process.
 */
export async function exitCode(process) {
    if (process.exitCode !== null) {
        return process.exitCode;
    }
    return new Promise(resolve => process.once('close', resolve));
}
/**
 * Catch error from a child process.
 * Also captures stderr output.
 * @param process
 * @returns A promise that resolves to an Error if the process exited with a non-zero code, or null if it exited successfully.
 */
export async function catchProcessError(process) {
    let error = new Error('Process exited with non-zero code');
    let stderr = '';
    process.on('error', (err) => {
        error = err;
    });
    if (process.stderr) {
        let chunk;
        for await (chunk of process.stderr) {
            stderr += chunk.toString();
        }
    }
    const code = await exitCode(process);
    if (stderr) {
        error = new Error(stderr);
    }
    return code ? error : null;
}
/**
 * Throws an error if the child process exits with a non-zero code.
 * @param process
 */
export async function throwProcessError(process) {
    const error = await catchProcessError(process);
    if (error) {
        throw error;
    }
}
/**
 * Yields the stdout of a child process.
 * It will throw an error if the process exits with a non-zero code.
 * @param process
 * @yields The stdout of the process.
 */
export async function* outputStream(process) {
    const { stdout } = process;
    const errorPromise = catchProcessError(process);
    if (stdout) {
        stdout.on('error', (err) => {
            // Iteration was interrupted, e.g. by `break` or `return` in a for-await loop.
            if (err.name === 'AbortError' && process.exitCode === null) {
                process.kill('SIGKILL');
            }
        });
        yield* stdout;
    }
    // Handle error only if iteration was not interrupted.
    const error = await errorPromise;
    if (error) {
        throw error;
    }
}
/**
 * Collects the stdout of a child process into a single Buffer.
 * It will throw an error if the process exits with a non-zero code.
 * @param process
 * @returns A promise that resolves to a Buffer containing the stdout of the process.
 */
export function output(process) {
    return concatBufferStream(outputStream(process));
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaW5kZXguanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi9zcmMvaW5kZXgudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQ0EsT0FBTyxFQUFFLGtCQUFrQixFQUFFLE1BQU0sMkJBQTJCLENBQUE7QUFFOUQ7Ozs7R0FJRztBQUNILE1BQU0sQ0FBQyxLQUFLLFVBQVUsUUFBUSxDQUFDLE9BQXFCO0lBQ2xELElBQUksT0FBTyxDQUFDLFFBQVEsS0FBSyxJQUFJLEVBQUU7UUFDN0IsT0FBTyxPQUFPLENBQUMsUUFBUSxDQUFBO0tBQ3hCO0lBRUQsT0FBTyxJQUFJLE9BQU8sQ0FBUyxPQUFPLENBQUMsRUFBRSxDQUFDLE9BQU8sQ0FBQyxJQUFJLENBQUMsT0FBTyxFQUFFLE9BQU8sQ0FBQyxDQUFDLENBQUE7QUFDdkUsQ0FBQztBQUVEOzs7OztHQUtHO0FBQ0gsTUFBTSxDQUFDLEtBQUssVUFBVSxpQkFBaUIsQ0FBQyxPQUFxQjtJQUMzRCxJQUFJLEtBQUssR0FBRyxJQUFJLEtBQUssQ0FBQyxtQ0FBbUMsQ0FBQyxDQUFBO0lBQzFELElBQUksTUFBTSxHQUFHLEVBQUUsQ0FBQTtJQUVmLE9BQU8sQ0FBQyxFQUFFLENBQUMsT0FBTyxFQUFFLENBQUMsR0FBVSxFQUFFLEVBQUU7UUFDakMsS0FBSyxHQUFHLEdBQUcsQ0FBQTtJQUNiLENBQUMsQ0FBQyxDQUFBO0lBRUYsSUFBSSxPQUFPLENBQUMsTUFBTSxFQUFFO1FBQ2xCLElBQUksS0FBYSxDQUFBO1FBRWpCLElBQUksS0FBSyxFQUFFLEtBQUssSUFBSSxPQUFPLENBQUMsTUFBTSxFQUFFO1lBQ2xDLE1BQU0sSUFBSSxLQUFLLENBQUMsUUFBUSxFQUFFLENBQUE7U0FDM0I7S0FDRjtJQUVELE1BQU0sSUFBSSxHQUFHLE1BQU0sUUFBUSxDQUFDLE9BQU8sQ0FBQyxDQUFBO0lBRXBDLElBQUksTUFBTSxFQUFFO1FBQ1YsS0FBSyxHQUFHLElBQUksS0FBSyxDQUFDLE1BQU0sQ0FBQyxDQUFBO0tBQzFCO0lBRUQsT0FBTyxJQUFJLENBQUMsQ0FBQyxDQUFDLEtBQUssQ0FBQyxDQUFDLENBQUMsSUFBSSxDQUFBO0FBQzVCLENBQUM7QUFFRDs7O0dBR0c7QUFDSCxNQUFNLENBQUMsS0FBSyxVQUFVLGlCQUFpQixDQUFDLE9BQXFCO0lBQzNELE1BQU0sS0FBSyxHQUFHLE1BQU0saUJBQWlCLENBQUMsT0FBTyxDQUFDLENBQUE7SUFFOUMsSUFBSSxLQUFLLEVBQUU7UUFDVCxNQUFNLEtBQUssQ0FBQTtLQUNaO0FBQ0gsQ0FBQztBQUVEOzs7OztHQUtHO0FBQ0gsTUFBTSxDQUFDLEtBQUssU0FBUyxDQUFDLENBQUMsWUFBWSxDQUFDLE9BQXFCO0lBQ3ZELE1BQU0sRUFBRSxNQUFNLEVBQUUsR0FBRyxPQUFPLENBQUE7SUFDMUIsTUFBTSxZQUFZLEdBQUcsaUJBQWlCLENBQUMsT0FBTyxDQUFDLENBQUE7SUFFL0MsSUFBSSxNQUFNLEVBQUU7UUFDVixNQUFNLENBQUMsRUFBRSxDQUFDLE9BQU8sRUFBRSxDQUFDLEdBQUcsRUFBRSxFQUFFO1lBQ3pCLDhFQUE4RTtZQUM5RSxJQUFJLEdBQUcsQ0FBQyxJQUFJLEtBQUssWUFBWSxJQUFJLE9BQU8sQ0FBQyxRQUFRLEtBQUssSUFBSSxFQUFFO2dCQUMxRCxPQUFPLENBQUMsSUFBSSxDQUFDLFNBQVMsQ0FBQyxDQUFBO2FBQ3hCO1FBQ0gsQ0FBQyxDQUFDLENBQUE7UUFFRixLQUFLLENBQUMsQ0FBQyxNQUErQixDQUFBO0tBQ3ZDO0lBRUQsc0RBQXNEO0lBRXRELE1BQU0sS0FBSyxHQUFHLE1BQU0sWUFBWSxDQUFBO0lBRWhDLElBQUksS0FBSyxFQUFFO1FBQ1QsTUFBTSxLQUFLLENBQUE7S0FDWjtBQUNILENBQUM7QUFFRDs7Ozs7R0FLRztBQUNILE1BQU0sVUFBVSxNQUFNLENBQUMsT0FBcUI7SUFDMUMsT0FBTyxrQkFBa0IsQ0FBQyxZQUFZLENBQUMsT0FBTyxDQUFDLENBQUMsQ0FBQTtBQUNsRCxDQUFDIn0=