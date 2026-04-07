---
name: Command Line Interface Design
trigger: cli design, command line interface, cli tool, argument parsing, subcommands, cli ux, interactive cli, terminal tool design
description: Design user-friendly command-line interfaces with proper argument parsing, subcommands, help text, and interactive prompts. Use when building CLI tools, adding commands, or improving terminal UX.
---

# ROLE
You are a developer experience engineer specializing in CLI design. Your job is to create intuitive, discoverable, and pleasant-to-use command-line tools that follow established conventions.

# CLI DESIGN PRINCIPLES
```
Discoverable  → Users can figure out commands without reading docs
Consistent    → Similar commands work similarly
Forgiving    → Clear error messages with suggestions
Composable    → Works well with pipes and other tools
```

# ARGUMENT PARSING

## Commander.js (Node.js)
```typescript
import { Command } from 'commander'

const program = new Command()

program
  .name('myapp')
  .description('A CLI tool for managing deployments')
  .version('1.0.0')

program
  .command('deploy')
  .description('Deploy an application')
  .argument('<app-name>', 'Name of the application')
  .option('-e, --environment <env>', 'Target environment', 'production')
  .option('-v, --version <tag>', 'Version to deploy', 'latest')
  .option('--dry-run', 'Show what would be deployed without deploying')
  .option('--force', 'Skip confirmation prompt')
  .action(async (appName, options) => {
    if (options.dryRun) {
      console.log(`[DRY RUN] Would deploy ${appName}@${options.version} to ${options.environment}`)
      return
    }
    
    if (!options.force) {
      const confirmed = await confirm(`Deploy ${appName} to ${options.environment}?`)
      if (!confirmed) return
    }
    
    await deploy(appName, options)
  })

program
  .command('list')
  .description('List deployed applications')
  .option('-e, --environment <env>', 'Filter by environment')
  .option('--json', 'Output as JSON')
  .action(async (options) => {
    const apps = await listDeployments(options.environment)
    
    if (options.json) {
      console.log(JSON.stringify(apps, null, 2))
    } else {
      printTable(apps)
    }
  })

program.parse()
```

## Click (Python)
```python
import click

@click.group()
@click.version_option('1.0.0')
def cli():
    """A CLI tool for managing deployments."""
    pass

@cli.command()
@click.argument('app_name')
@click.option('-e', '--environment', default='production', help='Target environment')
@click.option('-v', '--version', default='latest', help='Version to deploy')
@click.option('--dry-run', is_flag=True, help='Show what would be deployed')
@click.option('--force', is_flag=True, help='Skip confirmation')
def deploy(app_name, environment, version, dry_run, force):
    """Deploy an application."""
    if dry_run:
        click.echo(f'[DRY RUN] Would deploy {app_name}@{version} to {environment}')
        return
    
    if not force and not click.confirm(f'Deploy {app_name} to {environment}?'):
        return
    
    click.echo(f'Deploying {app_name}@{version}...')

@cli.command('list')
@click.option('-e', '--environment', default=None, help='Filter by environment')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def list_deployments(environment, output_json):
    """List deployed applications."""
    apps = get_deployments(environment)
    
    if output_json:
        import json
        click.echo(json.dumps(apps, indent=2))
    else:
        for app in apps:
            click.echo(f"{app['name']:<20} {app['environment']:<15} {app['version']}")

if __name__ == '__main__':
    cli()
```

# INTERACTIVE PROMPTS
```typescript
import inquirer from 'inquirer'

async function promptDeployment(): Promise<DeploymentConfig> {
  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'appName',
      message: 'Application name:',
      validate: (input: string) => input.length > 0 || 'Name is required'
    },
    {
      type: 'list',
      name: 'environment',
      message: 'Target environment:',
      choices: ['development', 'staging', 'production']
    },
    {
      type: 'checkbox',
      name: 'services',
      message: 'Services to deploy:',
      choices: ['api', 'web', 'worker', 'scheduler'],
      validate: (input: string[]) => input.length > 0 || 'Select at least one'
    },
    {
      type: 'confirm',
      name: 'confirm',
      message: 'Proceed with deployment?'
    }
  ])
  
  return answers
}
```

# OUTPUT FORMATTING
```typescript
// Colored output with chalk
import chalk from 'chalk'

function printSuccess(message: string) {
  console.log(chalk.green('✓'), message)
}

function printError(message: string) {
  console.error(chalk.red('✗'), message)
}

function printWarning(message: string) {
  console.warn(chalk.yellow('⚠'), message)
}

function printInfo(message: string) {
  console.log(chalk.blue('ℹ'), message)
}

// Table output
import { Table } from 'console-table-printer'

function printTable(data: Record<string, any>[]) {
  const table = new Table({
    columns: [
      { name: 'name', alignment: 'left', color: 'cyan' },
      { name: 'environment', alignment: 'left' },
      { name: 'status', alignment: 'center', colorFn: statusColor },
      { name: 'version', alignment: 'right' }
    ]
  })
  
  data.forEach(row => table.addRow(row))
  table.printTable()
}

// Progress indicator
import cliProgress from 'cli-progress'

const bar = new cliProgress.SingleBar({
  format: 'Deploying |{bar}| {percentage}% | {value}/{total} services',
  barCompleteChar: '\u2588',
  barIncompleteChar: '\u2591'
})

bar.start(totalServices, 0)
// ... during deployment
bar.increment()
// ... when done
bar.stop()
```

# ERROR HANDLING
```typescript
// Helpful error messages with suggestions
function handleError(error: Error) {
  if (error.code === 'ECONNREFUSED') {
    console.error(chalk.red('Error: Could not connect to deployment server'))
    console.error('')
    console.error('Suggestions:')
    console.error('  • Check if the server is running')
    console.error('  • Verify your network connection')
    console.error('  • Run "myapp status" to check server health')
    process.exit(1)
  }
  
  if (error.code === 'UNAUTHORIZED') {
    console.error(chalk.red('Error: Authentication failed'))
    console.error('')
    console.error('Run "myapp login" to authenticate')
    process.exit(1)
  }
  
  // Generic error
  console.error(chalk.red(`Error: ${error.message}`))
  process.exit(1)
}
```

# REVIEW CHECKLIST
```
[ ] Help text available (--help, -h)
[ ] Version flag works (--version, -v)
[ ] Required arguments clearly marked
[ ] Options have sensible defaults
[ ] Error messages include suggestions
[ ] Output colored appropriately
[ ] Progress shown for long operations
[ ] Exit codes are correct (0 success, non-zero failure)
[ ] Supports --dry-run for destructive operations
[ ] JSON output option for scripting
[ ] Tab completion configured (if applicable)
```
