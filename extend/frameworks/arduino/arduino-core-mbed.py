import os

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

FRAMEWORK_DIR = platform.get_package_dir("framework-arduino-mbed")
assert os.path.isdir(FRAMEWORK_DIR)


def load_flags(filename):
    if not filename:
        return []

    file_path = os.path.join(FRAMEWORK_DIR, "variants", board.get(
        "build.variant"), "%s.txt" % filename)
    if not os.path.isfile(file_path):
        print("Warning: Couldn't find file '%s'" % file_path)
        return []

    with open(file_path, "r") as fp:
        return [f.strip() for f in fp.readlines() if f.strip()]


cflags = set(load_flags("cflags"))
cxxflags = set(load_flags("cxxflags"))
ccflags = cflags.intersection(cxxflags)

env.Append(
    ASFLAGS=["-x", "assembler-with-cpp"],

    CFLAGS=sorted(list(cflags - ccflags)),

    CCFLAGS=sorted(list(ccflags)),

    CPPDEFINES=[d.replace("-D", "") for d in load_flags("defines")],

    CXXFLAGS=sorted(list(cxxflags - ccflags)),

    LIBPATH=[
        os.path.join(FRAMEWORK_DIR, "variants", board.get("build.variant")),
        os.path.join(FRAMEWORK_DIR, "variants", board.get("build.variant"), "libs")
    ],

    LINKFLAGS=load_flags("ldflags"),

    LIBSOURCE_DIRS=[os.path.join(FRAMEWORK_DIR, "libraries")],

    LIBS=["mbed"]
)

if board.get("build.mcu", "").startswith("nrf52"):
    env.Append(LIBS=["cc_310_core", "cc_310_ext", "cc_310_trng"])

env.Append(
    ASFLAGS=env.get("CCFLAGS", [])[:],

    # Due to long path names "-iprefix" hook is required to avoid toolchain crashes
    CCFLAGS=[
        "-iprefix" + os.path.join(FRAMEWORK_DIR, "cores", board.get("build.core")),
        "@%s" % os.path.join(FRAMEWORK_DIR, "variants", board.get(
            "build.variant"), "includes.txt"),
        "-nostdlib"
    ],

    CPPDEFINES=[
        ("ARDUINO", 10810),
        "ARDUINO_ARCH_MBED"
    ],

    CPPPATH=[
        os.path.join(FRAMEWORK_DIR, "cores", board.get("build.core")),
        os.path.join(FRAMEWORK_DIR, "cores", board.get(
            "build.core"), "api", "deprecated")
    ],

    LINKFLAGS=[
        "--specs=nano.specs",
        "--specs=nosys.specs",
        "-Wl,--as-needed"
    ]
)

# Framework requires all symbols from mbed libraries
env.Prepend(_LIBFLAGS="-Wl,--whole-archive ")
env.Append(_LIBFLAGS=" -Wl,--no-whole-archive -lstdc++ -lsupc++ -lm -lc -lgcc -lnosys")

if not board.get("build.ldscript", ""):
    env.Replace(LDSCRIPT_PATH=board.get("build.arduino.ldscript", ""))

libs = []

if "build.variant" in board:
    env.Append(CPPPATH=[
        os.path.join(FRAMEWORK_DIR, "variants", board.get("build.variant"))
    ])

    libs.append(
        env.BuildLibrary(
            os.path.join("$BUILD_DIR", "FrameworkArduinoVariant"),
            os.path.join(FRAMEWORK_DIR, "variants", board.get("build.variant"))))

libs.append(
    env.BuildLibrary(
        os.path.join("$BUILD_DIR", "FrameworkArduino"),
        os.path.join(FRAMEWORK_DIR, "cores", board.get("build.core"))))

env.Prepend(LIBS=libs)
