import { Readable } from 'stream';
/**
 * Get all items from an async iterable and return them as an array.
 * @param iterable
 * @returns A promise that resolves to an array of items.
 */
export async function toArray(iterable) {
    const result = [];
    for await (const item of iterable) {
        result.push(item);
    }
    return result;
}
/**
 * Concatenate all buffers from an async iterable into a single Buffer.
 * @param iterable
 * @returns A promise that resolves to a single Buffer containing all concatenated buffers.
 */
export async function concatBufferStream(iterable) {
    return Buffer.concat(await toArray(iterable));
}
/**
 * Concatenate all strings from an async iterable into a single string.
 * @param iterable
 * @returns A promise that resolves to a single string containing all concatenated strings.
 */
export async function concatStringStream(iterable) {
    return (await toArray(iterable)).join('');
}
/**
 * Get the first item from an async iterable.
 * @param stream
 * @returns A promise that resolves to the first item, or null if the iterable is empty.
 */
export async function firstFromStream(stream) {
    for await (const tag of stream) {
        return tag;
    }
    return null;
}
/**
 * Merges multiple Readable streams into a single Readable stream.
 * Each chunk will be an object containing the source stream name and the chunk data.
 * @param streams - An object where keys are stream names and values are Readable streams.
 * @returns A merged Readable stream.
 */
export function mergeReadables(streams) {
    const mergedStream = new Readable({
        objectMode: true,
        read() {
            /* no-op */
        }
    });
    let ended = 0;
    Object.entries(streams).forEach(([name, stream], _i, entries) => {
        stream
            .on('data', (chunk) => mergedStream.push({
            source: name,
            chunk
        }))
            .on('end', () => {
            ended += 1;
            if (ended === entries.length) {
                mergedStream.push(null);
            }
        })
            .on('error', err => mergedStream.destroy(err));
    });
    return mergedStream;
}
/**
 * Split stream by separator.
 * @param stream
 * @param separator
 * @yields String chunks.
 */
export async function* splitStream(stream, separator) {
    let chunk;
    let payload;
    let buffer = '';
    for await (chunk of stream) {
        buffer += chunk.toString();
        if (buffer.includes(separator)) {
            payload = buffer.split(separator);
            buffer = payload.pop() || '';
            yield* payload;
        }
    }
    if (buffer) {
        yield buffer;
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaW5kZXguanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi9zcmMvaW5kZXgudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUEsT0FBTyxFQUFFLFFBQVEsRUFBRSxNQUFNLFFBQVEsQ0FBQTtBQUVqQzs7OztHQUlHO0FBQ0gsTUFBTSxDQUFDLEtBQUssVUFBVSxPQUFPLENBQUksUUFBMEI7SUFDekQsTUFBTSxNQUFNLEdBQVEsRUFBRSxDQUFBO0lBRXRCLElBQUksS0FBSyxFQUFFLE1BQU0sSUFBSSxJQUFJLFFBQVEsRUFBRTtRQUNqQyxNQUFNLENBQUMsSUFBSSxDQUFDLElBQUksQ0FBQyxDQUFBO0tBQ2xCO0lBRUQsT0FBTyxNQUFNLENBQUE7QUFDZixDQUFDO0FBRUQ7Ozs7R0FJRztBQUNILE1BQU0sQ0FBQyxLQUFLLFVBQVUsa0JBQWtCLENBQUMsUUFBK0I7SUFDdEUsT0FBTyxNQUFNLENBQUMsTUFBTSxDQUFDLE1BQU0sT0FBTyxDQUFDLFFBQVEsQ0FBQyxDQUFDLENBQUE7QUFDL0MsQ0FBQztBQUVEOzs7O0dBSUc7QUFDSCxNQUFNLENBQUMsS0FBSyxVQUFVLGtCQUFrQixDQUFDLFFBQStCO0lBQ3RFLE9BQU8sQ0FBQyxNQUFNLE9BQU8sQ0FBQyxRQUFRLENBQUMsQ0FBQyxDQUFDLElBQUksQ0FBQyxFQUFFLENBQUMsQ0FBQTtBQUMzQyxDQUFDO0FBRUQ7Ozs7R0FJRztBQUNILE1BQU0sQ0FBQyxLQUFLLFVBQVUsZUFBZSxDQUFJLE1BQXdCO0lBQy9ELElBQUksS0FBSyxFQUFFLE1BQU0sR0FBRyxJQUFJLE1BQU0sRUFBRTtRQUM5QixPQUFPLEdBQUcsQ0FBQTtLQUNYO0lBRUQsT0FBTyxJQUFJLENBQUE7QUFDYixDQUFDO0FBT0Q7Ozs7O0dBS0c7QUFDSCxNQUFNLFVBQVUsY0FBYyxDQUk1QixPQUE0QjtJQUU1QixNQUFNLFlBQVksR0FBRyxJQUFJLFFBQVEsQ0FBQztRQUNoQyxVQUFVLEVBQUUsSUFBSTtRQUNoQixJQUFJO1lBQ0YsV0FBVztRQUNiLENBQUM7S0FDRixDQUFDLENBQUE7SUFDRixJQUFJLEtBQUssR0FBRyxDQUFDLENBQUE7SUFFYixNQUFNLENBQUMsT0FBTyxDQUFDLE9BQW1DLENBQUMsQ0FBQyxPQUFPLENBQUMsQ0FBQyxDQUFDLElBQUksRUFBRSxNQUFNLENBQUMsRUFBRSxFQUFFLEVBQUUsT0FBTyxFQUFFLEVBQUU7UUFDMUYsTUFBTTthQUNILEVBQUUsQ0FBQyxNQUFNLEVBQUUsQ0FBQyxLQUFhLEVBQUUsRUFBRSxDQUFDLFlBQVksQ0FBQyxJQUFJLENBQUM7WUFDL0MsTUFBTSxFQUFFLElBQUk7WUFDWixLQUFLO1NBQ04sQ0FBQyxDQUFDO2FBQ0YsRUFBRSxDQUFDLEtBQUssRUFBRSxHQUFHLEVBQUU7WUFDZCxLQUFLLElBQUksQ0FBQyxDQUFBO1lBRVYsSUFBSSxLQUFLLEtBQUssT0FBTyxDQUFDLE1BQU0sRUFBRTtnQkFDNUIsWUFBWSxDQUFDLElBQUksQ0FBQyxJQUFJLENBQUMsQ0FBQTthQUN4QjtRQUNILENBQUMsQ0FBQzthQUNELEVBQUUsQ0FBQyxPQUFPLEVBQUUsR0FBRyxDQUFDLEVBQUUsQ0FBQyxZQUFZLENBQUMsT0FBTyxDQUFDLEdBQUcsQ0FBQyxDQUFDLENBQUE7SUFDbEQsQ0FBQyxDQUFDLENBQUE7SUFFRixPQUFPLFlBQVksQ0FBQTtBQUNyQixDQUFDO0FBRUQ7Ozs7O0dBS0c7QUFDSCxNQUFNLENBQUMsS0FBSyxTQUFTLENBQUMsQ0FBQyxXQUFXLENBQUMsTUFBc0MsRUFBRSxTQUFpQjtJQUMxRixJQUFJLEtBQXNCLENBQUE7SUFDMUIsSUFBSSxPQUFpQixDQUFBO0lBQ3JCLElBQUksTUFBTSxHQUFHLEVBQUUsQ0FBQTtJQUVmLElBQUksS0FBSyxFQUFFLEtBQUssSUFBSSxNQUFNLEVBQUU7UUFDMUIsTUFBTSxJQUFJLEtBQUssQ0FBQyxRQUFRLEVBQUUsQ0FBQTtRQUUxQixJQUFJLE1BQU0sQ0FBQyxRQUFRLENBQUMsU0FBUyxDQUFDLEVBQUU7WUFDOUIsT0FBTyxHQUFHLE1BQU0sQ0FBQyxLQUFLLENBQUMsU0FBUyxDQUFDLENBQUE7WUFDakMsTUFBTSxHQUFHLE9BQU8sQ0FBQyxHQUFHLEVBQUUsSUFBSSxFQUFFLENBQUE7WUFFNUIsS0FBSyxDQUFDLENBQUMsT0FBTyxDQUFBO1NBQ2Y7S0FDRjtJQUVELElBQUksTUFBTSxFQUFFO1FBQ1YsTUFBTSxNQUFNLENBQUE7S0FDYjtBQUNILENBQUMifQ==