# λ-2D

λ-2D is a two-dimensional programming language inspired by
- [Piet](https://www.dangermouse.net/esoteric/piet.html) an esoteric programming language in which programs look like abstract paintings
- [Lambda Calculus](https://en.wikipedia.org/wiki/Lambda_calculus) a formal system in mathematical logic for expressing computation based on function abstraction and application using variable binding and substitution
- [Lambda Diagrams](https://tromp.github.io/cl/diagrams.html) a visual representation of lambda calculus

The language was designed by Lingdong Huang and is presented in his [blog post](https://www.media.mit.edu/projects/2d-an-exploration-of-drawing-as-programming-language-featuring-ideas-from-lambda-calculus/overview/).
An online-demo is available [here](https://l-2d.glitch.me/).


## Improvements

The interpreter is quite inefficient.
One can improve it by:
- using memoization to avoid recalculating the diagram values
- compiling the diagram to a program (similar as explained in the blog post)
- writing the interpreter in a more efficient language (e.g. Rust or OCaml)
- using an intermediate representation of the diagram (e.g. a graph) instead of a direct interpretation of the diagram

Note that trivial improvements (numba jit compilation, pypy, caching, ...) are not directly applicable to the current python code.