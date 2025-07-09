import { spawn } from 'child_process';
import { firstFromStream, splitStream } from '@simple-libs/stream-utils';
import { output, outputStream } from '@simple-libs/child-process-utils';
import { formatArgs, toArray } from './utils.js';
const SCISSOR = '------------------------ >8 ------------------------';
/**
 * Wrapper around Git CLI.
 */
export class GitClient {
    cwd;
    debug;
    constructor(cwd, debug) {
        this.cwd = cwd;
        this.debug = debug;
    }
    formatArgs(...args) {
        const finalArgs = formatArgs(...args);
        if (this.debug) {
            this.debug(finalArgs);
        }
        return finalArgs;
    }
    /**
     * Raw exec method to run git commands.
     * @param args
     * @returns Stdout string output of the command.
     */
    async exec(...args) {
        return (await output(spawn('git', this.formatArgs(...args), {
            cwd: this.cwd
        }))).toString().trim();
    }
    /**
     * Raw exec method to run git commands with stream output.
     * @param args
     * @returns Stdout stream of the command.
     */
    execStream(...args) {
        return outputStream(spawn('git', this.formatArgs(...args), {
            cwd: this.cwd
        }));
    }
    /**
     * Initialize a new git repository.
     * @returns Boolean result.
     */
    async init() {
        try {
            await this.exec('init');
            return true;
        }
        catch (err) {
            return false;
        }
    }
    /**
     * Get raw commits stream.
     * @param params
     * @param params.path - Read commits from specific path.
     * @param params.from - Start commits range.
     * @param params.to - End commits range.
     * @param params.format - Commits format.
     * @yields Raw commits data.
     */
    async *getRawCommits(params = {}) {
        const { path, from = '', to = 'HEAD', format = '%B', ignore, reverse, merges, since } = params;
        const shouldNotIgnore = ignore
            ? (chunk) => !ignore.test(chunk)
            : () => true;
        const stdout = this.execStream('log', `--format=${format}%n${SCISSOR}`, since && `--since=${since instanceof Date ? since.toISOString() : since}`, reverse && '--reverse', merges && '--merges', merges === false && '--no-merges', [from, to].filter(Boolean).join('..'), ...path ? ['--', ...toArray(path)] : []);
        const commitsStream = splitStream(stdout, `${SCISSOR}\n`);
        let chunk;
        for await (chunk of commitsStream) {
            if (shouldNotIgnore(chunk)) {
                yield chunk;
            }
        }
    }
    /**
     * Get tags stream.
     * @param params
     * @yields Tags
     */
    async *getTags(params = {}) {
        const { path, from = '', to = 'HEAD', since } = params;
        const tagRegex = /tag:\s*(.+?)[,)]/gi;
        const stdout = this.execStream('log', '--decorate', '--no-color', '--date-order', since && `--since=${since instanceof Date ? since.toISOString() : since}`, [from, to].filter(Boolean).join('..'), ...path ? ['--', ...toArray(path)] : []);
        let chunk;
        let matches;
        let tag;
        for await (chunk of stdout) {
            matches = chunk.toString().trim().matchAll(tagRegex);
            for ([, tag] of matches) {
                yield tag;
            }
        }
    }
    /**
     * Get last tag.
     * @param params
     * @returns Last tag, `null` if not found.
     */
    async getLastTag(params) {
        return firstFromStream(this.getTags(params));
    }
    /**
     * Check file is ignored via .gitignore.
     * @param file - Path to target file.
     * @returns Boolean value.
     */
    async checkIgnore(file) {
        try {
            await this.exec('check-ignore', '--', file);
            return true;
        }
        catch (err) {
            return false;
        }
    }
    /**
     * Add files to git index.
     * @param files - Files to stage.
     */
    async add(files) {
        await this.exec('add', '--', ...toArray(files));
    }
    /**
     * Commit changes.
     * @param params
     * @param params.verify
     * @param params.sign
     * @param params.files
     * @param params.allowEmpty
     * @param params.message
     */
    async commit(params) {
        const { verify = true, sign = false, files = [], allowEmpty = false, message } = params;
        await this.exec('commit', !verify && '--no-verify', sign && '-S', allowEmpty && '--allow-empty', '-m', message, '--', ...files);
    }
    /**
     * Create a tag for the current commit.
     * @param params
     * @param params.sign
     * @param params.name
     * @param params.message
     */
    async tag(params) {
        let { sign = false, name, message } = params;
        if (sign) {
            message = '';
        }
        await this.exec('tag', sign && '-s', message && '-a', ...message ? ['-m', message] : [], '--', name);
    }
    /**
     * Get current branch name.
     * @returns Current branch name.
     */
    async getCurrentBranch() {
        const branch = await this.exec('rev-parse', '--abbrev-ref', 'HEAD');
        return branch;
    }
    /**
     * Get default branch name.
     * @returns Default branch name.
     */
    async getDefaultBranch() {
        const branch = (await this.exec('rev-parse', '--abbrev-ref', 'origin/HEAD')).replace(/^origin\//, '');
        return branch;
    }
    /**
     * Push changes to remote.
     * @param branch
     * @param params
     * @param params.verify
     */
    async push(branch, params = {}) {
        const { verify = true, tags = false, followTags = false, force = false } = params;
        await this.exec('push', followTags && '--follow-tags', tags && '--tags', !verify && '--no-verify', force && '--force', 'origin', '--', branch);
    }
    /**
     * Verify rev exists.
     * @param rev
     * @param safe - If `true`, will not throw error if rev not found.
     * @returns Target hash.
     */
    async verify(rev, safe) {
        let git = this.exec('rev-parse', '--verify', rev);
        if (safe) {
            git = git.catch(() => '');
        }
        return await git;
    }
    /**
     * Get config value by key.
     * @param key - Config key.
     * @returns Config value.
     */
    async getConfig(key) {
        return await this.exec('config', '--get', '--', key);
    }
    /**
     * Set config value by key.
     * @param key - Config key.
     * @param value - Config value.
     */
    async setConfig(key, value) {
        await this.exec('config', '--', key, value);
    }
    /**
     * Fetch changes from remote.
     * @param params
     */
    async fetch(params = {}) {
        const { prune = false, unshallow = false, tags = false, all = false, remote, branch } = params;
        await this.exec('fetch', prune && '--prune', unshallow && '--unshallow', tags && '--tags', all && '--all', ...remote && branch ? [
            '--',
            remote,
            branch
        ] : []);
    }
    /**
     * Create a new branch.
     * @param branch - Branch name.
     */
    async createBranch(branch) {
        await this.exec('checkout', '-b', branch);
    }
    /**
     * Delete a branch.
     * @param branch - Branch name.
     */
    async deleteBranch(branch) {
        await this.exec('branch', '-D', '--', branch);
    }
    /**
     * Checkout a branch.
     * @param branch - Branch name.
     */
    async checkout(branch) {
        await this.exec('checkout', branch);
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiR2l0Q2xpZW50LmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vc3JjL0dpdENsaWVudC50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQSxPQUFPLEVBQUUsS0FBSyxFQUFFLE1BQU0sZUFBZSxDQUFBO0FBQ3JDLE9BQU8sRUFDTCxlQUFlLEVBQ2YsV0FBVyxFQUNaLE1BQU0sMkJBQTJCLENBQUE7QUFDbEMsT0FBTyxFQUNMLE1BQU0sRUFDTixZQUFZLEVBQ2IsTUFBTSxrQ0FBa0MsQ0FBQTtBQUN6QyxPQUFPLEVBQ0wsVUFBVSxFQUNWLE9BQU8sRUFDUixNQUFNLFlBQVksQ0FBQTtBQVduQixNQUFNLE9BQU8sR0FBRyxzREFBc0QsQ0FBQTtBQUV0RTs7R0FFRztBQUNILE1BQU0sT0FBTyxTQUFTO0lBRVQ7SUFDRjtJQUZULFlBQ1csR0FBVyxFQUNiLEtBQTZDO1FBRDNDLFFBQUcsR0FBSCxHQUFHLENBQVE7UUFDYixVQUFLLEdBQUwsS0FBSyxDQUF3QztJQUNuRCxDQUFDO0lBRUksVUFBVSxDQUFDLEdBQUcsSUFBVztRQUMvQixNQUFNLFNBQVMsR0FBRyxVQUFVLENBQUMsR0FBRyxJQUFJLENBQUMsQ0FBQTtRQUVyQyxJQUFJLElBQUksQ0FBQyxLQUFLLEVBQUU7WUFDZCxJQUFJLENBQUMsS0FBSyxDQUFDLFNBQVMsQ0FBQyxDQUFBO1NBQ3RCO1FBRUQsT0FBTyxTQUFTLENBQUE7SUFDbEIsQ0FBQztJQUVEOzs7O09BSUc7SUFDSCxLQUFLLENBQUMsSUFBSSxDQUFDLEdBQUcsSUFBVztRQUN2QixPQUFPLENBQ0wsTUFBTSxNQUFNLENBQUMsS0FBSyxDQUFDLEtBQUssRUFBRSxJQUFJLENBQUMsVUFBVSxDQUFDLEdBQUcsSUFBSSxDQUFDLEVBQUU7WUFDbEQsR0FBRyxFQUFFLElBQUksQ0FBQyxHQUFHO1NBQ2QsQ0FBQyxDQUFDLENBQ0osQ0FBQyxRQUFRLEVBQUUsQ0FBQyxJQUFJLEVBQUUsQ0FBQTtJQUNyQixDQUFDO0lBRUQ7Ozs7T0FJRztJQUNILFVBQVUsQ0FBQyxHQUFHLElBQVc7UUFDdkIsT0FBTyxZQUFZLENBQUMsS0FBSyxDQUFDLEtBQUssRUFBRSxJQUFJLENBQUMsVUFBVSxDQUFDLEdBQUcsSUFBSSxDQUFDLEVBQUU7WUFDekQsR0FBRyxFQUFFLElBQUksQ0FBQyxHQUFHO1NBQ2QsQ0FBQyxDQUFDLENBQUE7SUFDTCxDQUFDO0lBRUQ7OztPQUdHO0lBQ0gsS0FBSyxDQUFDLElBQUk7UUFDUixJQUFJO1lBQ0YsTUFBTSxJQUFJLENBQUMsSUFBSSxDQUFDLE1BQU0sQ0FBQyxDQUFBO1lBRXZCLE9BQU8sSUFBSSxDQUFBO1NBQ1o7UUFBQyxPQUFPLEdBQUcsRUFBRTtZQUNaLE9BQU8sS0FBSyxDQUFBO1NBQ2I7SUFDSCxDQUFDO0lBRUQ7Ozs7Ozs7O09BUUc7SUFDSCxLQUFLLENBQUEsQ0FBRSxhQUFhLENBQUMsU0FBdUIsRUFBRTtRQUM1QyxNQUFNLEVBQ0osSUFBSSxFQUNKLElBQUksR0FBRyxFQUFFLEVBQ1QsRUFBRSxHQUFHLE1BQU0sRUFDWCxNQUFNLEdBQUcsSUFBSSxFQUNiLE1BQU0sRUFDTixPQUFPLEVBQ1AsTUFBTSxFQUNOLEtBQUssRUFDTixHQUFHLE1BQU0sQ0FBQTtRQUNWLE1BQU0sZUFBZSxHQUFHLE1BQU07WUFDNUIsQ0FBQyxDQUFDLENBQUMsS0FBYSxFQUFFLEVBQUUsQ0FBQyxDQUFDLE1BQU0sQ0FBQyxJQUFJLENBQUMsS0FBSyxDQUFDO1lBQ3hDLENBQUMsQ0FBQyxHQUFHLEVBQUUsQ0FBQyxJQUFJLENBQUE7UUFDZCxNQUFNLE1BQU0sR0FBRyxJQUFJLENBQUMsVUFBVSxDQUM1QixLQUFLLEVBQ0wsWUFBWSxNQUFNLEtBQUssT0FBTyxFQUFFLEVBQ2hDLEtBQUssSUFBSSxXQUFXLEtBQUssWUFBWSxJQUFJLENBQUMsQ0FBQyxDQUFDLEtBQUssQ0FBQyxXQUFXLEVBQUUsQ0FBQyxDQUFDLENBQUMsS0FBSyxFQUFFLEVBQ3pFLE9BQU8sSUFBSSxXQUFXLEVBQ3RCLE1BQU0sSUFBSSxVQUFVLEVBQ3BCLE1BQU0sS0FBSyxLQUFLLElBQUksYUFBYSxFQUNqQyxDQUFDLElBQUksRUFBRSxFQUFFLENBQUMsQ0FBQyxNQUFNLENBQUMsT0FBTyxDQUFDLENBQUMsSUFBSSxDQUFDLElBQUksQ0FBQyxFQUNyQyxHQUFHLElBQUksQ0FBQyxDQUFDLENBQUMsQ0FBQyxJQUFJLEVBQUUsR0FBRyxPQUFPLENBQUMsSUFBSSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsRUFBRSxDQUN4QyxDQUFBO1FBQ0QsTUFBTSxhQUFhLEdBQUcsV0FBVyxDQUFDLE1BQU0sRUFBRSxHQUFHLE9BQU8sSUFBSSxDQUFDLENBQUE7UUFDekQsSUFBSSxLQUFhLENBQUE7UUFFakIsSUFBSSxLQUFLLEVBQUUsS0FBSyxJQUFJLGFBQWEsRUFBRTtZQUNqQyxJQUFJLGVBQWUsQ0FBQyxLQUFLLENBQUMsRUFBRTtnQkFDMUIsTUFBTSxLQUFLLENBQUE7YUFDWjtTQUNGO0lBQ0gsQ0FBQztJQUVEOzs7O09BSUc7SUFDSCxLQUFLLENBQUEsQ0FBRSxPQUFPLENBQUMsU0FBMkIsRUFBRTtRQUMxQyxNQUFNLEVBQ0osSUFBSSxFQUNKLElBQUksR0FBRyxFQUFFLEVBQ1QsRUFBRSxHQUFHLE1BQU0sRUFDWCxLQUFLLEVBQ04sR0FBRyxNQUFNLENBQUE7UUFDVixNQUFNLFFBQVEsR0FBRyxvQkFBb0IsQ0FBQTtRQUNyQyxNQUFNLE1BQU0sR0FBRyxJQUFJLENBQUMsVUFBVSxDQUM1QixLQUFLLEVBQ0wsWUFBWSxFQUNaLFlBQVksRUFDWixjQUFjLEVBQ2QsS0FBSyxJQUFJLFdBQVcsS0FBSyxZQUFZLElBQUksQ0FBQyxDQUFDLENBQUMsS0FBSyxDQUFDLFdBQVcsRUFBRSxDQUFDLENBQUMsQ0FBQyxLQUFLLEVBQUUsRUFDekUsQ0FBQyxJQUFJLEVBQUUsRUFBRSxDQUFDLENBQUMsTUFBTSxDQUFDLE9BQU8sQ0FBQyxDQUFDLElBQUksQ0FBQyxJQUFJLENBQUMsRUFDckMsR0FBRyxJQUFJLENBQUMsQ0FBQyxDQUFDLENBQUMsSUFBSSxFQUFFLEdBQUcsT0FBTyxDQUFDLElBQUksQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLEVBQUUsQ0FDeEMsQ0FBQTtRQUNELElBQUksS0FBYSxDQUFBO1FBQ2pCLElBQUksT0FBMkMsQ0FBQTtRQUMvQyxJQUFJLEdBQVcsQ0FBQTtRQUVmLElBQUksS0FBSyxFQUFFLEtBQUssSUFBSSxNQUFNLEVBQUU7WUFDMUIsT0FBTyxHQUFHLEtBQUssQ0FBQyxRQUFRLEVBQUUsQ0FBQyxJQUFJLEVBQUUsQ0FBQyxRQUFRLENBQUMsUUFBUSxDQUFDLENBQUE7WUFFcEQsS0FBSyxDQUFDLEVBQUUsR0FBRyxDQUFDLElBQUksT0FBTyxFQUFFO2dCQUN2QixNQUFNLEdBQUcsQ0FBQTthQUNWO1NBQ0Y7SUFDSCxDQUFDO0lBRUQ7Ozs7T0FJRztJQUNILEtBQUssQ0FBQyxVQUFVLENBQUMsTUFBeUI7UUFDeEMsT0FBTyxlQUFlLENBQUMsSUFBSSxDQUFDLE9BQU8sQ0FBQyxNQUFNLENBQUMsQ0FBQyxDQUFBO0lBQzlDLENBQUM7SUFFRDs7OztPQUlHO0lBQ0gsS0FBSyxDQUFDLFdBQVcsQ0FBQyxJQUFZO1FBQzVCLElBQUk7WUFDRixNQUFNLElBQUksQ0FBQyxJQUFJLENBQ2IsY0FBYyxFQUNkLElBQUksRUFDSixJQUFJLENBQ0wsQ0FBQTtZQUVELE9BQU8sSUFBSSxDQUFBO1NBQ1o7UUFBQyxPQUFPLEdBQUcsRUFBRTtZQUNaLE9BQU8sS0FBSyxDQUFBO1NBQ2I7SUFDSCxDQUFDO0lBRUQ7OztPQUdHO0lBQ0gsS0FBSyxDQUFDLEdBQUcsQ0FBQyxLQUF3QjtRQUNoQyxNQUFNLElBQUksQ0FBQyxJQUFJLENBQ2IsS0FBSyxFQUNMLElBQUksRUFDSixHQUFHLE9BQU8sQ0FBQyxLQUFLLENBQUMsQ0FDbEIsQ0FBQTtJQUNILENBQUM7SUFFRDs7Ozs7Ozs7T0FRRztJQUNILEtBQUssQ0FBQyxNQUFNLENBQUMsTUFBdUI7UUFDbEMsTUFBTSxFQUNKLE1BQU0sR0FBRyxJQUFJLEVBQ2IsSUFBSSxHQUFHLEtBQUssRUFDWixLQUFLLEdBQUcsRUFBRSxFQUNWLFVBQVUsR0FBRyxLQUFLLEVBQ2xCLE9BQU8sRUFDUixHQUFHLE1BQU0sQ0FBQTtRQUVWLE1BQU0sSUFBSSxDQUFDLElBQUksQ0FDYixRQUFRLEVBQ1IsQ0FBQyxNQUFNLElBQUksYUFBYSxFQUN4QixJQUFJLElBQUksSUFBSSxFQUNaLFVBQVUsSUFBSSxlQUFlLEVBQzdCLElBQUksRUFDSixPQUFPLEVBQ1AsSUFBSSxFQUNKLEdBQUcsS0FBSyxDQUNULENBQUE7SUFDSCxDQUFDO0lBRUQ7Ozs7OztPQU1HO0lBQ0gsS0FBSyxDQUFDLEdBQUcsQ0FBQyxNQUFvQjtRQUM1QixJQUFJLEVBQ0YsSUFBSSxHQUFHLEtBQUssRUFDWixJQUFJLEVBQ0osT0FBTyxFQUNSLEdBQUcsTUFBTSxDQUFBO1FBRVYsSUFBSSxJQUFJLEVBQUU7WUFDUixPQUFPLEdBQUcsRUFBRSxDQUFBO1NBQ2I7UUFFRCxNQUFNLElBQUksQ0FBQyxJQUFJLENBQ2IsS0FBSyxFQUNMLElBQUksSUFBSSxJQUFJLEVBQ1osT0FBTyxJQUFJLElBQUksRUFDZixHQUFHLE9BQU8sQ0FBQyxDQUFDLENBQUMsQ0FBQyxJQUFJLEVBQUUsT0FBTyxDQUFDLENBQUMsQ0FBQyxDQUFDLEVBQUUsRUFDakMsSUFBSSxFQUNKLElBQUksQ0FDTCxDQUFBO0lBQ0gsQ0FBQztJQUVEOzs7T0FHRztJQUNILEtBQUssQ0FBQyxnQkFBZ0I7UUFDcEIsTUFBTSxNQUFNLEdBQUcsTUFBTSxJQUFJLENBQUMsSUFBSSxDQUM1QixXQUFXLEVBQ1gsY0FBYyxFQUNkLE1BQU0sQ0FDUCxDQUFBO1FBRUQsT0FBTyxNQUFNLENBQUE7SUFDZixDQUFDO0lBRUQ7OztPQUdHO0lBQ0gsS0FBSyxDQUFDLGdCQUFnQjtRQUNwQixNQUFNLE1BQU0sR0FBRyxDQUNiLE1BQU0sSUFBSSxDQUFDLElBQUksQ0FDYixXQUFXLEVBQ1gsY0FBYyxFQUNkLGFBQWEsQ0FDZCxDQUNGLENBQUMsT0FBTyxDQUFDLFdBQVcsRUFBRSxFQUFFLENBQUMsQ0FBQTtRQUUxQixPQUFPLE1BQU0sQ0FBQTtJQUNmLENBQUM7SUFFRDs7Ozs7T0FLRztJQUNILEtBQUssQ0FBQyxJQUFJLENBQ1IsTUFBYyxFQUNkLFNBQXdCLEVBQUU7UUFFMUIsTUFBTSxFQUNKLE1BQU0sR0FBRyxJQUFJLEVBQ2IsSUFBSSxHQUFHLEtBQUssRUFDWixVQUFVLEdBQUcsS0FBSyxFQUNsQixLQUFLLEdBQUcsS0FBSyxFQUNkLEdBQUcsTUFBTSxDQUFBO1FBRVYsTUFBTSxJQUFJLENBQUMsSUFBSSxDQUNiLE1BQU0sRUFDTixVQUFVLElBQUksZUFBZSxFQUM3QixJQUFJLElBQUksUUFBUSxFQUNoQixDQUFDLE1BQU0sSUFBSSxhQUFhLEVBQ3hCLEtBQUssSUFBSSxTQUFTLEVBQ2xCLFFBQVEsRUFDUixJQUFJLEVBQ0osTUFBTSxDQUNQLENBQUE7SUFDSCxDQUFDO0lBRUQ7Ozs7O09BS0c7SUFDSCxLQUFLLENBQUMsTUFBTSxDQUFDLEdBQVcsRUFBRSxJQUFjO1FBQ3RDLElBQUksR0FBRyxHQUFHLElBQUksQ0FBQyxJQUFJLENBQ2pCLFdBQVcsRUFDWCxVQUFVLEVBQ1YsR0FBRyxDQUNKLENBQUE7UUFFRCxJQUFJLElBQUksRUFBRTtZQUNSLEdBQUcsR0FBRyxHQUFHLENBQUMsS0FBSyxDQUFDLEdBQUcsRUFBRSxDQUFDLEVBQUUsQ0FBQyxDQUFBO1NBQzFCO1FBRUQsT0FBTyxNQUFNLEdBQUcsQ0FBQTtJQUNsQixDQUFDO0lBRUQ7Ozs7T0FJRztJQUNILEtBQUssQ0FBQyxTQUFTLENBQUMsR0FBVztRQUN6QixPQUFPLE1BQU0sSUFBSSxDQUFDLElBQUksQ0FDcEIsUUFBUSxFQUNSLE9BQU8sRUFDUCxJQUFJLEVBQ0osR0FBRyxDQUNKLENBQUE7SUFDSCxDQUFDO0lBRUQ7Ozs7T0FJRztJQUNILEtBQUssQ0FBQyxTQUFTLENBQUMsR0FBVyxFQUFFLEtBQWE7UUFDeEMsTUFBTSxJQUFJLENBQUMsSUFBSSxDQUNiLFFBQVEsRUFDUixJQUFJLEVBQ0osR0FBRyxFQUNILEtBQUssQ0FDTixDQUFBO0lBQ0gsQ0FBQztJQUVEOzs7T0FHRztJQUNILEtBQUssQ0FBQyxLQUFLLENBQUMsU0FBeUIsRUFBRTtRQUNyQyxNQUFNLEVBQ0osS0FBSyxHQUFHLEtBQUssRUFDYixTQUFTLEdBQUcsS0FBSyxFQUNqQixJQUFJLEdBQUcsS0FBSyxFQUNaLEdBQUcsR0FBRyxLQUFLLEVBQ1gsTUFBTSxFQUNOLE1BQU0sRUFDUCxHQUFHLE1BQU0sQ0FBQTtRQUVWLE1BQU0sSUFBSSxDQUFDLElBQUksQ0FDYixPQUFPLEVBQ1AsS0FBSyxJQUFJLFNBQVMsRUFDbEIsU0FBUyxJQUFJLGFBQWEsRUFDMUIsSUFBSSxJQUFJLFFBQVEsRUFDaEIsR0FBRyxJQUFJLE9BQU8sRUFDZCxHQUFHLE1BQU0sSUFBSSxNQUFNLENBQUMsQ0FBQyxDQUFDO1lBQ3BCLElBQUk7WUFDSixNQUFNO1lBQ04sTUFBTTtTQUNQLENBQUMsQ0FBQyxDQUFDLEVBQUUsQ0FDUCxDQUFBO0lBQ0gsQ0FBQztJQUVEOzs7T0FHRztJQUNILEtBQUssQ0FBQyxZQUFZLENBQUMsTUFBYztRQUMvQixNQUFNLElBQUksQ0FBQyxJQUFJLENBQ2IsVUFBVSxFQUNWLElBQUksRUFDSixNQUFNLENBQ1AsQ0FBQTtJQUNILENBQUM7SUFFRDs7O09BR0c7SUFDSCxLQUFLLENBQUMsWUFBWSxDQUFDLE1BQWM7UUFDL0IsTUFBTSxJQUFJLENBQUMsSUFBSSxDQUNiLFFBQVEsRUFDUixJQUFJLEVBQ0osSUFBSSxFQUNKLE1BQU0sQ0FDUCxDQUFBO0lBQ0gsQ0FBQztJQUVEOzs7T0FHRztJQUNILEtBQUssQ0FBQyxRQUFRLENBQUMsTUFBYztRQUMzQixNQUFNLElBQUksQ0FBQyxJQUFJLENBQ2IsVUFBVSxFQUNWLE1BQU0sQ0FDUCxDQUFBO0lBQ0gsQ0FBQztDQUNGIn0=