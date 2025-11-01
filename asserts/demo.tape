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
Type "echo '=== Package Domain ==='"
Enter
Sleep 2s

Type "echo '1. Basic Package Manager Commands'"
Enter
Sleep 2s

Type "bbe map -t pacman -- brew uninstall vim"
Enter
Sleep 2s
Ctrl+A
Sleep 2s
Type "sudo "
Sleep 2s
Ctrl+C
Sleep 2s

Type "bbe map -t pacman -- brew search vim"
Enter
Sleep 2s
Enter
Sleep 2s

Type "bbe map -t pacman -- brew install vim"
Enter
Sleep 2s
Ctrl+A
Sleep 2s
Type "sudo "
Sleep 2s
Ctrl+C
Sleep 2s

Type "bbe map -t pacman -- brew info vim"
Enter
Sleep 2s
Enter
Sleep 2s

Type "bbe map -t pacman -- brew list -v vim"
Enter
Sleep 2s
Enter
Sleep 2s

Type "echo '2. Operation Mappings'"
Enter
Sleep 2s

Type "bbe op -t pacman -- "
Sleep 2s
Tab
Sleep 2s
Type "list_installed"
Sleep 2s
Enter
Sleep 2s
Enter
Sleep 2s
Enter
Sleep 2s

Type "echo '3. List Mappings'"
Enter
Sleep 2s

Type "cmdbridge list cmd-mappings -s brew -t pacman"
Enter
Sleep 6s

Type "cmdbridge list op-cmds -t pacman"
Enter
Sleep 6s

Type "echo '=== Firewall Domain ==='"
Enter
Sleep 2s

Type "echo '1. Map mufw to iptables'"
Enter
Sleep 2s

Type "bbe map -t iptables -- mufw allow --port 8888 --proto tcp"
Enter
Sleep 2s
Ctrl+C
Sleep 2s

Type "bbe map -t iptables -- mufw delete allow --port 8888 --proto tcp"
Enter
Sleep 2s
Ctrl+C
Sleep 2s

Type "echo '2. Map iptables to mufw'"
Enter
Sleep 2s

Type "bbe map -t mufw -- iptables -A INPUT -p tcp --dport 8888 -j ACCEPT"
Enter
Sleep 2s
Ctrl+C
Sleep 2s

Type "bbe map -t mufw -- iptables -D INPUT -p tcp --dport 8888 -j ACCEPT"
Enter
Sleep 2s
Ctrl+C
Sleep 2s
