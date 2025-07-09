import type { GetCommitsParams, GetSemverTagsParams } from '@conventional-changelog/git-client';
import type { Options } from '../types.js';
export declare function parseOptions(options: Record<string, unknown>): Options | null;
export declare function parseTagsOptions(options: Record<string, unknown>): GetSemverTagsParams | null;
export declare function parseCommitsOptions(options: Record<string, unknown>): GetCommitsParams | null;
//# sourceMappingURL=options.d.ts.map