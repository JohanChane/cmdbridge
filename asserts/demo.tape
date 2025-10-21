# demo.tape
Output demo.gif
Set Shell "zsh"

Set FontSize 32
Set Width 2560
Set Height 1440

Set TypingSpeed 0.00
Type "source ~/.zshrc; cd ~"
Enter
Ctrl+L
Set TypingSpeed 0.10

Sleep 1s
Type "echo '=== CmdBridge Demo ==='"
Enter
Sleep 1s

Type "echo '1. Basic Package Manager Commands'"
Enter
Sleep 0.5s

Type "ame map brew uninstall vim"
Enter
Sleep 3s
Ctrl+A
Sleep 2s
Type "sudo "
Sleep 3s
Ctrl+C
Sleep 3s

Type "ame map brew search vim"
Enter
Sleep 3s
Enter
Sleep 3s

Type "ame map brew install vim"
Enter
Sleep 3s
Ctrl+A
Sleep 2s
Type "sudo "
Sleep 3s
Ctrl+C
Sleep 3s

Type "ame map brew info vim"
Enter
Sleep 3s
Enter
Sleep 3s

Type "ame map brew ls -v vim"
Enter
Sleep 3s
Enter
Sleep 3s

Sleep 0.5s
Type "echo '2. Direct Action Execution'"
Enter
Sleep 0.5s

Type "ame act "
Sleep 3s
Tab
Sleep 3s
Type "info"
Sleep 3s
Enter
Sleep 1s
Type " vim"
Sleep 3s
Enter
Sleep 3s
Enter

Type "echo '3. System Information'"
Enter
Sleep 0.5s

Type "cmdbridge --list-cmdbridges"
Enter
Sleep 6s

Type "cmdbridge --output-cmdbridge brew pacman"
Enter
Sleep 6s

Type "cmdbridge --output-cmdbridge brew pip"
Enter
Sleep 6s
