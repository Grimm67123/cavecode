"""
Tests for all 9 language compressors in CaveCode.
Verifies that:
1. Comments are 100% preserved in dense telegraphic format.
2. Function, class, and variable names are 100% preserved.
3. Function bodies and logic are NOT replaced with ellipsis (...).
4. Boilerplate and syntax noise are effectively compressed.
"""

from cavecode.compressors import get_compressor


def test_python_compressor():
    compressor = get_compressor("python")
    code = '''
# Critical comment: business logic calculation
from typing import (
    Dict,
    List,
    Optional,
    Union,
)

class Worker:
    """Class docstring must be preserved."""
    def __init__(self, name: Optional[str], age: Union[int, float]):
        # Keep this comment inside init
        self.name = name
        self.age = age

    def calculate(self, x: int) -> int:
        # Core algorithmic calculation
        total = 0
        for i in range(x):
            total += i * 2
        return total

if __name__ == '__main__':
    w = Worker("test", 25)
    print(w.calculate(10))
'''
    compressed = compressor.compress(code)

    # 1. Comments preserved
    assert "Critical comment" in compressed
    assert "Keep this comment" in compressed
    assert "algorithmic calculation" in compressed
    assert '"""Class docstring' in compressed

    # 2. Names preserved
    assert "class Worker:" in compressed
    assert "calculate" in compressed
    assert "total" in compressed

    # 3. Logic intact (not stubbed with ...)
    assert "total += i * 2" in compressed
    assert "ret total" in compressed or "return total" in compressed
    assert "..." not in compressed

    # 4. Boilerplate compressed
    assert "Optional[" not in compressed
    assert len(compressed) < len(code)


def test_java_compressor():
    compressor = get_compressor("java")
    code = '''
// Important Java license comment
package com.example.service;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.HashMap;

public class UserService {
    // Keep user state
    private String name;
    private int age;

    public String getName() {
        return this.name;
    }
    public void setName(String name) {
        this.name = name;
    }

    public int computeHash(int multiplier) {
        // Essential algorithm logic
        int result = 42;
        for (int i = 0; i < age; i++) {
            result += i * multiplier;
        }
        return result;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        UserService that = (UserService) o;
        return age == that.age && Objects.equals(name, that.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, age);
    }

    @Override
    public String toString() {
        return "UserService{" + "name='" + name + '\'' + ", age=" + age + '}';
    }
}
'''
    compressed = compressor.compress(code)

    # 1. Comments preserved
    assert "Important Java license comment" in compressed
    assert "Keep user state" in compressed
    assert "algorithm logic" in compressed

    # 2. Names preserved
    assert "UserService" in compressed
    assert "computeHash" in compressed
    assert "getName" in compressed

    # 3. Logic intact
    assert "result += i * multiplier" in compressed
    assert "ret result" in compressed or "return result" in compressed

    # 4. Boilerplate compressed
    assert "pub class UserService" in compressed
    assert "@Override" not in compressed
    assert len(compressed) < len(code)


def test_csharp_compressor():
    compressor = get_compressor("csharp")
    code = '''
// Header comment for C# service
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace MyCompany.Orders {
    public class OrderProcessor {
        // Injected repo
        private readonly IOrderRepo _repo;
        private readonly ILogger _logger;

        public OrderProcessor(IOrderRepo repo, ILogger logger) {
            _repo = repo;
            _logger = logger;
        }

        public async Task<int> Process(int orderId) {
            // Compute order amount
            int total = orderId * 100;
            await Task.Delay(10);
            return total;
        }
    }
}
'''
    compressed = compressor.compress(code)

    # Comments and names
    assert "Header comment" in compressed
    assert "Injected repo" in compressed
    assert "Compute order amount" in compressed
    assert "OrderProcessor" in compressed
    assert "total = orderId * 100" in compressed

    # Compression
    assert "pub class OrderProcessor" in compressed
    assert "using System" in compressed
    assert len(compressed) < len(code)


def test_cpp_and_c_compressor():
    cpp_comp = get_compressor("cpp")
    c_comp = get_compressor("c")

    cpp_code = '''
// Header comment for math utils
#ifndef MATH_UTILS_H
#define MATH_UTILS_H

#include <vector>
#include <string>
#include <memory>
#include <iostream>

namespace Math {
namespace Engine {

class Solver {
public:
    // Core compute method
    std::vector<int> solve(int n) {
        std::vector<int> results;
        for (int i = 0; i < n; ++i) {
            results.push_back(i * 3);
        }
        return results;
    }
};

}
}
#endif
'''
    compressed_cpp = cpp_comp.compress(cpp_code)
    assert "Header comment" in compressed_cpp
    assert "Core compute method" in compressed_cpp
    assert "results.push_back(i * 3)" in compressed_cpp
    assert "/* [guard MATH_UTILS_H] */ #pragma once" in compressed_cpp
    assert "#include <vector, string, memory, iostream>" in compressed_cpp
    assert "vector<int> solve" in compressed_cpp  # std:: stripped
    assert "namespace Math::Engine {" in compressed_cpp
    assert len(compressed_cpp) < len(cpp_code)

    c_code = '''
// C standard library module
#ifndef UTILS_H
#define UTILS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int add(int a, int b) {
    // Add two ints
    return a + b;
}
#endif
'''
    compressed_c = c_comp.compress(c_code)
    assert "C standard library module" in compressed_c
    assert "Add two ints" in compressed_c
    assert "ret a + b" in compressed_c or "return a + b" in compressed_c
    assert "/* [guard UTILS_H] */ #pragma once" in compressed_c
    assert "#include <stdio.h, stdlib.h, string.h>" in compressed_c


def test_go_compressor():
    compressor = get_compressor("go")
    code = '''
// Package comment
package handler

import (
    "fmt"
    "os"
    "context"
)

func ProcessUser(ctx context.Context, id string) (string, error) {
    // Validate user
    user, err := fetchUser(ctx, id)
    if err != nil {
        return "", err
    }

    // Do complex business logic
    formatted := fmt.Sprintf("User: %s", user.Name)
    return formatted, nil
}
'''
    compressed = compressor.compress(code)

    assert "pkg comment" in compressed or "Package comment" in compressed
    assert "Validate user" in compressed
    assert "business logic" in compressed
    assert "ProcessUser" in compressed
    assert "formatted := fmt.Sprintf" in compressed
    assert "if err != nil { ret \"\", err }" in compressed or "if err != nil { return \"\", err }" in compressed
    assert 'import ("fmt" "os" "context")' in compressed
    assert len(compressed) < len(code)


def test_rust_compressor():
    compressor = get_compressor("rust")
    code = '''
// Rust data models
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Account {
    // Account ID
    pub id: u64,
    pub balance: i64,
}

impl Account {
    pub fn deposit(&mut self, amount: i64) -> Result<(), String> {
        // Check amount
        if amount <= 0 {
            return Err("Invalid amount".into());
        }
        self.balance += amount;
        Ok(())
    }
}
'''
    compressed = compressor.compress(code)

    assert "Rust data models" in compressed
    assert "Account ID" in compressed
    assert "Check amount" in compressed
    assert "pub struct Account" in compressed
    assert "self.balance += amount" in compressed
    assert "#[derive(Debug,Clone,PartialEq,Eq,Serialize,Deserialize)]" in compressed
    assert len(compressed) < len(code)


def test_javascript_typescript_compressor():
    compressor = get_compressor("typescript")
    code = '''
// React component comments
import {
    useState,
    useEffect,
    useCallback,
} from 'react';

export default function Counter() {
    // State hook
    const [count, setCount] = useState(0);

    const increment = () => {
        // Update count logic
        setCount(prev => prev + 1);
    };

    return <div>{count}</div>;
}
'''
    compressed = compressor.compress(code)

    assert "React component comments" in compressed
    assert "State hook" in compressed
    assert "Update count logic" in compressed
    assert "setCount(prev => prev + 1)" in compressed
    assert "import { useState, useEffect, useCallback } from 'react'" in compressed
    assert "Counter()" in compressed
    assert len(compressed) < len(code)


def test_modes_lite_medium_ultra():
    comp = get_compressor("python")
    code = """
# License comment
# Detailed comment
def heavy_func(a: int, b: int) -> int:
    \"\"\"Important docstring\"\"\"
    res = a + b
    return res
"""
    lite = comp.compress(code, mode="lite")
    med = comp.compress(code, mode="medium")
    ultra = comp.compress(code, mode="ultra")

    # Lite keeps docstring/comments and full body
    assert "Important docstring" in lite
    assert "res = a + b" in lite

    # Med keeps full body and telegraphic comments
    assert "res = a + b" in med

    # Ultra strips comments and docstrings, compacts body
    assert "Important docstring" not in ultra
    assert "pass" in ultra
    assert len(ultra) < len(med) <= len(lite)
