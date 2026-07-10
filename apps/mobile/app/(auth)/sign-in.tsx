import { Link, router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';

import { ActionButton } from '@/components/ActionButton';
import { Screen } from '@/components/Screen';
import { useSession } from '@/auth/useSession';
import { colors, radii, spacing, typography } from '@/theme/tokens';

export default function SignInScreen() {
  const { signIn, isConfigured } = useSession();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit() {
    setError(null);
    setIsSubmitting(true);
    try {
      await signIn(email.trim(), password);
      router.back();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in failed.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Screen title="Sign in" subtitle="Use the same Supabase account as the web app.">
      <View style={styles.panel}>
        {!isConfigured && (
          <Text style={styles.errorText}>
            Supabase env vars are missing. Add EXPO_PUBLIC_SUPABASE_URL and
            EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY.
          </Text>
        )}

        <TextInput
          autoCapitalize="none"
          autoComplete="email"
          autoCorrect={false}
          keyboardType="email-address"
          onChangeText={setEmail}
          placeholder="Email"
          placeholderTextColor={colors.muted}
          style={styles.input}
          value={email}
        />
        <TextInput
          autoCapitalize="none"
          onChangeText={setPassword}
          placeholder="Password"
          placeholderTextColor={colors.muted}
          secureTextEntry
          style={styles.input}
          value={password}
        />

        {error && <Text style={styles.errorText}>{error}</Text>}

        <ActionButton
          label={isSubmitting ? 'Signing in...' : 'Sign in'}
          onPress={handleSubmit}
          disabled={!isConfigured || isSubmitting || !email || !password}
        />

        <Link href="/sign-up" style={styles.link}>
          Create an account
        </Link>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  panel: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  input: {
    backgroundColor: colors.canvas,
    borderColor: colors.border,
    borderRadius: radii.md,
    borderWidth: 1,
    color: colors.text,
    fontSize: 16,
    minHeight: 50,
    paddingHorizontal: spacing.md,
  },
  errorText: {
    color: colors.danger,
    fontSize: typography.caption,
    lineHeight: 18,
  },
  link: {
    color: colors.accent,
    fontSize: typography.body,
    fontWeight: '800',
    textAlign: 'center',
  },
});
