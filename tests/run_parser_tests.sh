# test/run_parser_tests.sh
#!/bin/bash

echo "🧪 运行解析器测试套件..."

echo "📊 运行数据类型测试..."
python -m pytest tests/test_parsers/test_types.py -v

echo "🔧 运行 Getopt 解析器测试..."
python -m pytest tests/test_parsers/test_getopt.py -v

echo "🛠️ 运行 Argparse 解析器测试..."
python -m pytest tests/test_parsers/test_argparse.py -v

echo "🏭 运行工厂测试..."
python -m pytest tests/test_parsers/test_factory.py -v

echo "✅ 解析器测试完成!"