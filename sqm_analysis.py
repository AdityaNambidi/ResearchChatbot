#!/usr/bin/env python3
"""
Software Quality Metrics (SQM) Analysis Tool
Custom implementation without external metric libraries
Analyzes codebase for LOC, Cyclomatic Complexity, Halstead Metrics, and OO Metrics
"""

import os
import ast
import re
import math
from collections import defaultdict, Counter
from pathlib import Path
from tabulate import tabulate


class HalsteadMetrics(ast.NodeVisitor):
    """Calculate Halstead metrics from AST"""
    
    def __init__(self):
        self.operators = []
        self.operands = []
        
    def visit_BinOp(self, node):
        """Binary operators: +, -, *, /, //, %, **, @"""
        op_name = type(node.op).__name__
        self.operators.append(op_name)
        self.generic_visit(node)
    
    def visit_UnaryOp(self, node):
        """Unary operators: +, -, not, ~"""
        op_name = type(node.op).__name__
        self.operators.append(op_name)
        self.generic_visit(node)
    
    def visit_Compare(self, node):
        """Comparison operators: ==, !=, <, <=, >, >=, is, is not, in, not in"""
        for op in node.ops:
            op_name = type(op).__name__
            self.operators.append(op_name)
        self.generic_visit(node)
    
    def visit_BoolOp(self, node):
        """Boolean operators: and, or"""
        op_name = type(node.op).__name__
        self.operators.append(op_name)
        self.generic_visit(node)
    
    def visit_AugAssign(self, node):
        """Augmented assignment: +=, -=, *=, etc."""
        self.operators.append('AugAssign')
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Assignment: ="""
        self.operators.append('Assign')
        self.generic_visit(node)
    
    def visit_If(self, node):
        """If statement"""
        self.operators.append('If')
        self.generic_visit(node)
    
    def visit_For(self, node):
        """For loop"""
        self.operators.append('For')
        self.generic_visit(node)
    
    def visit_While(self, node):
        """While loop"""
        self.operators.append('While')
        self.generic_visit(node)
    
    def visit_With(self, node):
        """With statement"""
        self.operators.append('With')
        self.generic_visit(node)
    
    def visit_Try(self, node):
        """Try statement"""
        self.operators.append('Try')
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node):
        """Except handler"""
        self.operators.append('Except')
        self.generic_visit(node)
    
    def visit_Return(self, node):
        """Return statement"""
        self.operators.append('Return')
        self.generic_visit(node)
    
    def visit_Yield(self, node):
        """Yield statement"""
        self.operators.append('Yield')
        self.generic_visit(node)
    
    def visit_Raise(self, node):
        """Raise statement"""
        self.operators.append('Raise')
        self.generic_visit(node)
    
    def visit_Break(self, node):
        """Break statement"""
        self.operators.append('Break')
        self.generic_visit(node)
    
    def visit_Continue(self, node):
        """Continue statement"""
        self.operators.append('Continue')
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Function/method call"""
        self.operators.append('Call')
        self.generic_visit(node)
    
    def visit_Lambda(self, node):
        """Lambda expression"""
        self.operators.append('Lambda')
        self.generic_visit(node)
    
    def visit_IfExp(self, node):
        """Ternary expression: x if condition else y"""
        self.operators.append('IfExp')
        self.generic_visit(node)
    
    def visit_ListComp(self, node):
        """List comprehension"""
        self.operators.append('ListComp')
        self.generic_visit(node)
    
    def visit_DictComp(self, node):
        """Dict comprehension"""
        self.operators.append('DictComp')
        self.generic_visit(node)
    
    def visit_SetComp(self, node):
        """Set comprehension"""
        self.operators.append('SetComp')
        self.generic_visit(node)
    
    def visit_GeneratorExp(self, node):
        """Generator expression"""
        self.operators.append('GeneratorExp')
        self.generic_visit(node)
    
    def visit_Subscript(self, node):
        """Subscript: x[y]"""
        self.operators.append('Subscript')
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """Attribute access: x.y"""
        self.operators.append('Attribute')
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Variable/identifier name"""
        self.operands.append(node.id)
        self.generic_visit(node)
    
    def visit_Constant(self, node):
        """Constant value (Python 3.8+)"""
        if isinstance(node.value, (str, int, float, bool, bytes, type(None))):
            self.operands.append(repr(node.value))
        self.generic_visit(node)
    
    def visit_Num(self, node):
        """Number literal (Python < 3.8)"""
        self.operands.append(str(node.n))
        self.generic_visit(node)
    
    def visit_Str(self, node):
        """String literal (Python < 3.8)"""
        self.operands.append(repr(node.s))
        self.generic_visit(node)
    
    def visit_Bytes(self, node):
        """Bytes literal"""
        self.operands.append(repr(node.s))
        self.generic_visit(node)
    
    def visit_NameConstant(self, node):
        """Name constant: True, False, None (Python < 3.8)"""
        self.operands.append(str(node.value))
        self.generic_visit(node)
    
    def calculate(self):
        """Calculate Halstead metrics"""
        if not self.operators and not self.operands:
            return None
        
        # Distinct operators and operands
        h1 = len(set(self.operators))  # Distinct operators
        h2 = len(set(self.operands))    # Distinct operands
        
        # Total operators and operands
        N1 = len(self.operators)        # Total operators
        N2 = len(self.operands)         # Total operands
        
        # Vocabulary
        vocabulary = h1 + h2
        
        # Length
        length = N1 + N2
        
        # Calculated length
        calculated_length = h1 * math.log2(h1) + h2 * math.log2(h2) if h1 > 0 and h2 > 0 else 0
        
        # Volume
        volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
        
        # Difficulty
        difficulty = (h1 / 2) * (N2 / h2) if h2 > 0 else 0
        
        # Effort
        effort = difficulty * volume
        
        # Time (seconds)
        time = effort / 18  # Stroud number
        
        # Bugs
        bugs = volume / 3000 if volume > 0 else 0
        
        return {
            'h1': h1,
            'h2': h2,
            'N1': N1,
            'N2': N2,
            'vocabulary': vocabulary,
            'length': length,
            'calculated_length': calculated_length,
            'volume': volume,
            'difficulty': difficulty,
            'effort': effort,
            'time': time,
            'bugs': bugs
        }


class ComplexityVisitor(ast.NodeVisitor):
    """Calculate cyclomatic complexity"""
    
    def __init__(self):
        self.complexity = 1  # Base complexity
        self.functions = []
        self.current_function = None
        
    def visit_FunctionDef(self, node):
        """Visit function definition"""
        old_function = self.current_function
        self.current_function = {
            'name': node.name,
            'line': node.lineno,
            'complexity': 1  # Base complexity
        }
        
        # Visit function body
        self.generic_visit(node)
        
        self.functions.append(self.current_function)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node):
        """Visit async function definition"""
        self.visit_FunctionDef(node)
    
    def visit_If(self, node):
        """If statement adds 1 to complexity"""
        if self.current_function:
            self.current_function['complexity'] += 1
        self.generic_visit(node)
    
    def visit_For(self, node):
        """For loop adds 1 to complexity"""
        if self.current_function:
            self.current_function['complexity'] += 1
        self.generic_visit(node)
    
    def visit_AsyncFor(self, node):
        """Async for loop adds 1 to complexity"""
        if self.current_function:
            self.current_function['complexity'] += 1
        self.generic_visit(node)
    
    def visit_While(self, node):
        """While loop adds 1 to complexity"""
        if self.current_function:
            self.current_function['complexity'] += 1
        self.generic_visit(node)
    
    def visit_With(self, node):
        """With statement adds 1 to complexity"""
        if self.current_function:
            self.current_function['complexity'] += 1
        self.generic_visit(node)
    
    def visit_AsyncWith(self, node):
        """Async with statement adds 1 to complexity"""
        if self.current_function:
            self.current_function['complexity'] += 1
        self.generic_visit(node)
    
    def visit_Try(self, node):
        """Try statement adds 1 to complexity"""
        if self.current_function:
            self.current_function['complexity'] += 1
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node):
        """Exception handler adds 1 to complexity"""
        if self.current_function:
            self.current_function['complexity'] += 1
        self.generic_visit(node)
    
    def visit_BoolOp(self, node):
        """Boolean operations add complexity"""
        if self.current_function:
            # Each operator in 'and'/'or' adds 1
            self.current_function['complexity'] += len(node.values) - 1
        self.generic_visit(node)
    
    def visit_IfExp(self, node):
        """Ternary expression adds 1 to complexity"""
        if self.current_function:
            self.current_function['complexity'] += 1
        self.generic_visit(node)


class OOAnalyzer(ast.NodeVisitor):
    """Analyze Object-Oriented metrics"""
    
    def __init__(self):
        self.classes = []
        self.current_class = None
        
    def visit_ClassDef(self, node):
        """Visit class definition"""
        old_class = self.current_class
        self.current_class = {
            'name': node.name,
            'line': node.lineno,
            'methods': 0,
            'attributes': 0,
            'inheritance_depth': len(node.bases) if node.bases else 0
        }
        
        # Count methods and attributes
        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                self.current_class['methods'] += 1
            elif isinstance(item, ast.Assign):
                # Class-level assignments are attributes
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        self.current_class['attributes'] += 1
        
        self.generic_visit(node)
        self.classes.append(self.current_class)
        self.current_class = old_class


class SQMAnalyzer:
    def __init__(self, root_dir='.'):
        self.root_dir = Path(root_dir)
        self.loc_stats = defaultdict(int)
        self.complexity_stats = []
        self.halstead_stats = []
        self.oo_stats = {
            'classes': 0,
            'methods': 0,
            'attributes': 0,
            'inheritance_depth': []
        }
        
    def get_file_extensions(self):
        """Map file extensions to languages"""
        return {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.html': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.md': 'Markdown',
            '.txt': 'Text',
            '.yml': 'YAML',
            '.yaml': 'YAML'
        }
    
    def count_lines_of_code(self):
        """Count lines of code by language"""
        extensions = self.get_file_extensions()
        exclude_dirs = {'.git', '__pycache__', 'venv', 'env', '.venv', 'node_modules', '.pytest_cache'}
        exclude_files = {'.env', '.gitignore', '.env.example', 'sqm_analysis.py'}
        
        for file_path in self.root_dir.rglob('*'):
            if file_path.is_file():
                # Skip excluded directories
                if any(part in exclude_dirs for part in file_path.parts):
                    continue
                
                # Skip excluded files
                if file_path.name in exclude_files:
                    continue
                
                ext = file_path.suffix.lower()
                lang = extensions.get(ext, 'Other')
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        total_lines = len(lines)
                        blank_lines = sum(1 for line in lines if not line.strip())
                        code_lines = total_lines - blank_lines
                        
                        self.loc_stats[lang] += code_lines
                except Exception as e:
                    continue
        
        return self.loc_stats
    
    def analyze_python_complexity(self):
        """Analyze cyclomatic complexity of Python files"""
        exclude_dirs = {'.git', '__pycache__', 'venv', 'env', '.venv', 'node_modules', '.pytest_cache'}
        
        for py_file in self.root_dir.rglob('*.py'):
            # Skip this analysis script itself
            if py_file.name == 'sqm_analysis.py':
                continue
            
            if any(part in exclude_dirs for part in py_file.parts):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                tree = ast.parse(code, filename=str(py_file))
                visitor = ComplexityVisitor()
                visitor.visit(tree)
                
                for func in visitor.functions:
                    self.complexity_stats.append({
                        'file': str(py_file.relative_to(self.root_dir)),
                        'name': func['name'],
                        'type': 'function',
                        'complexity': func['complexity'],
                        'line': func['line']
                    })
            except SyntaxError:
                continue
            except Exception as e:
                continue
        
        return self.complexity_stats
    
    def analyze_halstead(self):
        """Analyze Halstead metrics for all Python files"""
        exclude_dirs = {'.git', '__pycache__', 'venv', 'env', '.venv', 'node_modules', '.pytest_cache'}
        
        for py_file in self.root_dir.rglob('*.py'):
            # Skip this analysis script itself
            if py_file.name == 'sqm_analysis.py':
                continue
            
            if any(part in exclude_dirs for part in py_file.parts):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                tree = ast.parse(code, filename=str(py_file))
                halstead = HalsteadMetrics()
                halstead.visit(tree)
                
                metrics = halstead.calculate()
                if metrics:
                    metrics['file'] = str(py_file.relative_to(self.root_dir))
                    self.halstead_stats.append(metrics)
            except SyntaxError:
                continue
            except Exception as e:
                continue
        
        return self.halstead_stats
    
    def analyze_oo_metrics(self):
        """Analyze Object-Oriented metrics"""
        exclude_dirs = {'.git', '__pycache__', 'venv', 'env', '.venv', 'node_modules', '.pytest_cache'}
        
        for py_file in self.root_dir.rglob('*.py'):
            # Skip this analysis script itself
            if py_file.name == 'sqm_analysis.py':
                continue
            
            if any(part in exclude_dirs for part in py_file.parts):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                tree = ast.parse(code, filename=str(py_file))
                analyzer = OOAnalyzer()
                analyzer.visit(tree)
                
                for cls in analyzer.classes:
                    self.oo_stats['classes'] += 1
                    self.oo_stats['methods'] += cls['methods']
                    self.oo_stats['attributes'] += cls['attributes']
                    self.oo_stats['inheritance_depth'].append(cls['inheritance_depth'])
            except SyntaxError:
                continue
            except Exception as e:
                continue
        
        return self.oo_stats
    
    def print_loc_table(self):
        """Print Lines of Code table"""
        loc_data = self.count_lines_of_code()
        if not loc_data:
            print("\nNo code files found.")
            return
        
        table_data = [[lang, lines] for lang, lines in sorted(loc_data.items(), key=lambda x: -x[1])]
        table_data.append(['TOTAL', sum(loc_data.values())])
        
        print("\n" + "="*60)
        print("LINES OF CODE (LOC) BY LANGUAGE")
        print("="*60)
        print(tabulate(table_data, headers=['Language', 'Lines of Code'], tablefmt='grid'))
    
    def print_complexity_table(self):
        """Print Cyclomatic Complexity table"""
        if not self.complexity_stats:
            print("\nNo complexity data found.")
            return
        
        # Summary statistics
        complexities = [stat['complexity'] for stat in self.complexity_stats]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        max_complexity = max(complexities) if complexities else 0
        min_complexity = min(complexities) if complexities else 0
        
        # Complexity distribution
        distribution = defaultdict(int)
        for c in complexities:
            if c <= 5:
                distribution['1-5 (Simple)'] += 1
            elif c <= 10:
                distribution['6-10 (Moderate)'] += 1
            elif c <= 20:
                distribution['11-20 (Complex)'] += 1
            else:
                distribution['21+ (Very Complex)'] += 1
        
        print("\n" + "="*60)
        print("CYCLOMATIC COMPLEXITY ANALYSIS")
        print("="*60)
        
        summary_data = [
            ['Total Functions/Methods', len(self.complexity_stats)],
            ['Average Complexity', f"{avg_complexity:.2f}"],
            ['Max Complexity', max_complexity],
            ['Min Complexity', min_complexity]
        ]
        print(tabulate(summary_data, headers=['Metric', 'Value'], tablefmt='grid'))
        
        print("\nComplexity Distribution:")
        dist_data = [[range, count] for range, count in sorted(distribution.items())]
        print(tabulate(dist_data, headers=['Complexity Range', 'Count'], tablefmt='grid'))
        
        # Top 10 most complex functions
        top_complex = sorted(self.complexity_stats, key=lambda x: x['complexity'], reverse=True)[:10]
        if top_complex:
            print("\nTop 10 Most Complex Functions/Methods:")
            complex_data = [[stat['file'], stat['name'], stat['type'], stat['complexity']] 
                            for stat in top_complex]
            print(tabulate(complex_data, headers=['File', 'Name', 'Type', 'Complexity'], tablefmt='grid'))
    
    def print_halstead_table(self):
        """Print Halstead Metrics table"""
        if not self.halstead_stats:
            print("\nNo Halstead metrics found.")
            return
        
        # Aggregate metrics across all files
        total_h1 = sum(stat['h1'] for stat in self.halstead_stats)
        total_h2 = sum(stat['h2'] for stat in self.halstead_stats)
        total_N1 = sum(stat['N1'] for stat in self.halstead_stats)
        total_N2 = sum(stat['N2'] for stat in self.halstead_stats)
        total_vocab = sum(stat['vocabulary'] for stat in self.halstead_stats)
        total_length = sum(stat['length'] for stat in self.halstead_stats)
        total_calc_length = sum(stat['calculated_length'] for stat in self.halstead_stats)
        total_volume = sum(stat['volume'] for stat in self.halstead_stats)
        total_difficulty = sum(stat['difficulty'] for stat in self.halstead_stats)
        total_effort = sum(stat['effort'] for stat in self.halstead_stats)
        total_time = sum(stat['time'] for stat in self.halstead_stats)
        total_bugs = sum(stat['bugs'] for stat in self.halstead_stats)
        
        avg_volume = total_volume / len(self.halstead_stats) if self.halstead_stats else 0
        avg_difficulty = total_difficulty / len(self.halstead_stats) if self.halstead_stats else 0
        avg_effort = total_effort / len(self.halstead_stats) if self.halstead_stats else 0
        
        print("\n" + "="*60)
        print("HALSTEAD METRICS")
        print("="*60)
        
        metrics_data = [
            ['n1 (Distinct Operators)', f"{total_h1:.2f}"],
            ['n2 (Distinct Operands)', f"{total_h2:.2f}"],
            ['N1 (Total Operators)', f"{total_N1:.2f}"],
            ['N2 (Total Operands)', f"{total_N2:.2f}"],
            ['Vocabulary (h1 + h2)', f"{total_vocab:.2f}"],
            ['Length (N1 + N2)', f"{total_length:.2f}"],
            ['Calculated Length', f"{total_calc_length:.2f}"],
            ['Volume', f"{total_volume:.2f}"],
            ['Difficulty', f"{total_difficulty:.2f}"],
            ['Effort', f"{total_effort:.2f}"],
            ['Time (seconds)', f"{total_time:.2f}"],
            ['Estimated Bugs', f"{total_bugs:.2f}"]
        ]
        
        print(tabulate(metrics_data, headers=['Metric', 'Value'], tablefmt='grid'))
        
        print("\nAverage Metrics per File:")
        avg_data = [
            ['Average Volume', f"{avg_volume:.2f}"],
            ['Average Difficulty', f"{avg_difficulty:.2f}"],
            ['Average Effort', f"{avg_effort:.2f}"]
        ]
        print(tabulate(avg_data, headers=['Metric', 'Value'], tablefmt='grid'))
    
    def print_oo_table(self):
        """Print Object-Oriented Metrics table"""
        oo_data = self.oo_stats
        
        avg_inheritance = sum(oo_data['inheritance_depth']) / len(oo_data['inheritance_depth']) if oo_data['inheritance_depth'] else 0
        max_inheritance = max(oo_data['inheritance_depth']) if oo_data['inheritance_depth'] else 0
        
        print("\n" + "="*60)
        print("OBJECT-ORIENTED METRICS")
        print("="*60)
        
        oo_table_data = [
            ['Total Classes', oo_data['classes']],
            ['Total Methods', oo_data['methods']],
            ['Total Attributes', oo_data['attributes']],
            ['Average Methods per Class', f"{oo_data['methods'] / oo_data['classes']:.2f}" if oo_data['classes'] > 0 else '0'],
            ['Average Attributes per Class', f"{oo_data['attributes'] / oo_data['classes']:.2f}" if oo_data['classes'] > 0 else '0'],
            ['Average Inheritance Depth', f"{avg_inheritance:.2f}"],
            ['Max Inheritance Depth', max_inheritance]
        ]
        
        print(tabulate(oo_table_data, headers=['Metric', 'Value'], tablefmt='grid'))
    
    def run_analysis(self):
        """Run complete SQM analysis"""
        print("\n" + "="*60)
        print("SOFTWARE QUALITY METRICS (SQM) ANALYSIS")
        print("="*60)
        print(f"Analyzing codebase in: {self.root_dir.absolute()}")
        
        # Run all analyses
        print("\nAnalyzing LOC...")
        self.count_lines_of_code()
        
        print("Analyzing Cyclomatic Complexity...")
        self.analyze_python_complexity()
        
        print("Analyzing Halstead Metrics...")
        self.analyze_halstead()
        
        print("Analyzing OO Metrics...")
        self.analyze_oo_metrics()
        
        # Print results
        self.print_loc_table()
        self.print_complexity_table()
        self.print_halstead_table()
        self.print_oo_table()
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60 + "\n")


def main():
    import sys
    
    root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    analyzer = SQMAnalyzer(root_dir)
    analyzer.run_analysis()


if __name__ == '__main__':
    main()
